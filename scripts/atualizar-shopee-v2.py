#!/usr/bin/env python3
"""Saber é Poder V4 — importador Shopee V2.

Uso local:
python atualizar-shopee.py --input "..\feeds\ARQUIVO.csv"

Produção:
defina SHOPEE_DATAFEED_URL no ambiente/GitHub Actions.

O campo "product_short link" é preservado como link de afiliado.
"""
import argparse, csv, json, os, re, sys, tempfile, urllib.request, unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_PRODUCTS = DATA / "produtos.json"
OUT_CATEGORIES = DATA / "categorias.json"

MAX_PRODUCTS = int(os.getenv("MAX_PRODUCTS", "10000"))
MAX_PER_CATEGORY = int(os.getenv("MAX_PER_CATEGORY", "1500"))

CATEGORY_MAP = {
    "Mobile & Gadgets": "Tecnologia",
    "Computers & Accessories": "Tecnologia",
    "Audio": "Tecnologia",
    "Cameras & Drones": "Tecnologia",
    "Gaming & Consoles": "Tecnologia",
    "Home Appliances": "Casa e Organização",
    "Home & Living": "Casa e Organização",
    "Beauty": "Beleza e Skincare",
    "Health": "Saúde e Bem-estar",
    "Mom & Baby": "Bebê e Infantil",
    "Baby & Kids Fashion": "Bebê e Infantil",
    "Women Clothes": "Moda e Acessórios",
    "Men Clothes": "Moda e Acessórios",
    "Fashion Accessories": "Moda e Acessórios",
    "Shoes": "Moda e Acessórios",
    "Sports & Outdoors": "Esportes e Lazer",
    "Pets": "Pets",
    "Food & Beverages": "Alimentos e Bebidas",
    "Books & Magazines": "Livros e Papelaria",
    "Hobbies & Collections": "Hobbies e Coleções",
    "Watches": "Moda e Acessórios",
}

def clean(v):
    return re.sub(r"\s+", " ", str(v or "").replace("\x00", " ")).strip()

def num(v):
    try: return float(str(v).replace(",", "."))
    except: return 0.0

def money(v):
    try: return round(float(str(v).replace(",", ".")), 2)
    except: return None

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def category(row):
    vals = [clean(row.get(k)) for k in ("global_category1","global_category2","global_category3")]
    for v in vals:
        if v in CATEGORY_MAP:
            return CATEGORY_MAP[v]
    # Segunda camada: procura palavras-chave no título/categorias.
    text = " ".join([clean(row.get("title")), *vals]).lower()
    rules = [
        (("beauty","makeup","skin","hair","perfume"), "Beleza e Skincare"),
        (("mobile","phone","tablet","computer","laptop","audio","headphone"), "Tecnologia"),
        (("baby","kids","mom","infant"), "Bebê e Infantil"),
        (("pet","dog","cat"), "Pets"),
        (("sport","fitness","outdoor"), "Esportes e Lazer"),
        (("health","vitamin","wellness"), "Saúde e Bem-estar"),
        (("home","kitchen","furniture","storage","decoration"), "Casa e Organização"),
    ]
    for words, cat in rules:
        if any(w in text for w in words):
            return cat
    return "Outros"

def affiliate(row):
    return clean(row.get("product_short link"))

def score(row):
    rating = min(num(row.get("item_rating")), 5)
    shop = min(num(row.get("shop_rating")), 5)
    discount = min(max(num(row.get("discount_percentage")), 0), 70)
    likes = max(num(row.get("like")), 0)
    return round(rating*12 + shop*5 + discount*.25 + likes**0.5, 3)

def normalize(row):
    title, image, link = clean(row.get("title")), clean(row.get("image_link")), affiliate(row)
    if not title or not image or not link: return None
    price = money(row.get("price"))
    sale = money(row.get("sale_price"))
    if sale is None: sale = price
    if sale is None: return None
    return {
        "id": clean(row.get("itemid")),
        "nome": title,
        "preco": sale,
        "preco_original": price,
        "desconto": num(row.get("discount_percentage")),
        "avaliacao": round(num(row.get("item_rating")), 2),
        "avaliacao_loja": round(num(row.get("shop_rating")), 2),
        "curtidas": int(num(row.get("like"))),
        "categoria": category(row),
        "categoria_shopee": clean(row.get("global_category1")),
        "subcategoria": clean(row.get("global_category2")),
        "loja": clean(row.get("shop_name")),
        "imagem": image,
        "link": link,
        "descricao": clean(row.get("description"))[:800],
        "pontuacao": score(row),
    }

def process(path):
    DATA.mkdir(parents=True, exist_ok=True)
    groups, seen = defaultdict(list), set()
    total = valid = 0
    with open(path, encoding="utf-8-sig", newline="", errors="replace") as f:
        reader = csv.DictReader(f)
        required = {"itemid","title","image_link","product_short link"}
        missing = required - set(reader.fieldnames or [])
        if missing: raise RuntimeError("Campos ausentes: " + ", ".join(sorted(missing)))
        for row in reader:
            total += 1
            p = normalize(row)
            if not p or not p["id"] or p["id"] in seen: continue
            seen.add(p["id"]); valid += 1; groups[p["categoria"]].append(p)

    products = []
    for cat, items in groups.items():
        items.sort(key=lambda x: x["pontuacao"], reverse=True)
        products.extend(items[:MAX_PER_CATEGORY])
    products.sort(key=lambda x: x["pontuacao"], reverse=True)
    products = products[:MAX_PRODUCTS]

    now = datetime.now(timezone.utc).isoformat()
    counts = Counter(p["categoria"] for p in products)
    cats = [{"nome": k, "slug": slug(k), "quantidade": counts[k]}
            for k in sorted(counts, key=lambda x: (-counts[x], x))]

    payload = {
        "version": 2,
        "source": "Shopee Affiliate Datafeed",
        "updated_at": now,
        "total_lidos": total,
        "total_aprovados": valid,
        "total_publicados": len(products),
        "products": products,
    }
    OUT_PRODUCTS.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    OUT_CATEGORIES.write_text(json.dumps({"version":2,"updated_at":now,"categories":cats}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Produtos lidos:       {total}")
    print(f"Produtos válidos:     {valid}")
    print(f"Produtos publicados:  {len(products)}")
    print(f"Categorias:           {len(cats)}")
    for c in cats: print(f"  - {c['nome']}: {c['quantidade']}")
    print(f"Gerado: {OUT_PRODUCTS}")
    print(f"Gerado: {OUT_CATEGORIES}")

def download(url):
    fd, p = tempfile.mkstemp(suffix=".csv"); os.close(fd)
    req = urllib.request.Request(url, headers={"User-Agent":"Saber-e-Poder-V4/2.0"})
    with urllib.request.urlopen(req, timeout=180) as r, open(p,"wb") as f:
        while True:
            b=r.read(1024*1024)
            if not b: break
            f.write(b)
    return Path(p)

ap = argparse.ArgumentParser()
ap.add_argument("--input")
args = ap.parse_args()
tmp = None
try:
    if args.input:
        path = Path(args.input)
        if not path.exists(): raise FileNotFoundError(path)
    else:
        url = os.getenv("SHOPEE_DATAFEED_URL","").strip()
        if not url: raise RuntimeError("Use --input arquivo.csv ou defina SHOPEE_DATAFEED_URL.")
        path = download(url); tmp = path
    process(path)
finally:
    if tmp and tmp.exists(): tmp.unlink()
