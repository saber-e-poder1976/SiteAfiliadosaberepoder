#!/usr/bin/env python3
"""
Saber é Poder Recomenda — Importador automático Shopee V4

IMPORTANTE:
- NÃO coloque o URL do datafeed dentro deste arquivo.
- Configure a variável de ambiente SHOPEE_DATAFEED_URL.
- O campo "product_short link" é usado como link de afiliado do feed.
- O script também pode receber um CSV local com --input para testes.

Exemplos:
    python scripts/atualizar-shopee.py --input feed.csv
    SHOPEE_DATAFEED_URL="..." python scripts/atualizar-shopee.py

Saídas:
    data/produtos.json
    data/categorias.json
"""

import argparse
import csv
import json
import os
import re
import sys
import tempfile
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DEFAULT_OUTPUT = DATA_DIR / "produtos.json"
DEFAULT_CATEGORIES = DATA_DIR / "categorias.json"

# Limites para manter o catálogo rápido.
# 10.000 é adequado para o feed menor; para 100.000 podemos ajustar depois.
MAX_PRODUCTS = int(os.getenv("MAX_PRODUCTS", "10000"))
MAX_PER_CATEGORY = int(os.getenv("MAX_PER_CATEGORY", "1000"))

# Mapeamento da Shopee para as categorias principais da V4.
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

def clean_text(value):
    if value is None:
        return ""
    value = str(value).replace("\x00", " ")
    return re.sub(r"\s+", " ", value).strip()

def money(value):
    try:
        return round(float(str(value).replace(",", ".")), 2)
    except (TypeError, ValueError):
        return None

def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def choose_category(row):
    for field in ("global_category1", "global_category2", "global_category3"):
        raw = clean_text(row.get(field))
        if raw in CATEGORY_MAP:
            return CATEGORY_MAP[raw]
    return "Outros"

def affiliate_url(row):
    # Confirmado nos dois CSVs enviados:
    # "product_short link" contém o redirecionamento de afiliado da Shopee.
    return clean_text(row.get("product_short link"))

def image_url(row):
    return clean_text(row.get("image_link")) or clean_text(row.get("image_link_3"))

def make_score(row):
    rating = number(row.get("item_rating"))
    discount = number(row.get("discount_percentage"))
    likes = number(row.get("like"))
    shop_rating = number(row.get("shop_rating"))

    # Pontuação simples e transparente.
    # Não representa ranking oficial da Shopee.
    score = (
        min(rating, 5) * 12
        + min(shop_rating, 5) * 5
        + min(discount, 70) * 0.25
        + min(likes, 10000) ** 0.5
    )
    return round(score, 3)

def normalize(row):
    title = clean_text(row.get("title"))
    image = image_url(row)
    affiliate = affiliate_url(row)

    if not title or not image or not affiliate:
        return None

    price = money(row.get("price"))
    sale_price = money(row.get("sale_price"))
    if sale_price is None:
        sale_price = price

    if price is None and sale_price is None:
        return None

    category = choose_category(row)

    return {
        "id": clean_text(row.get("itemid")),
        "nome": title,
        "preco": sale_price if sale_price is not None else price,
        "preco_original": price,
        "desconto": number(row.get("discount_percentage")),
        "avaliacao": round(number(row.get("item_rating")), 2),
        "avaliacao_loja": round(number(row.get("shop_rating")), 2),
        "curtidas": int(number(row.get("like"))),
        "categoria": category,
        "categoria_shopee": clean_text(row.get("global_category1")),
        "subcategoria": clean_text(row.get("global_category2")),
        "loja": clean_text(row.get("shop_name")),
        "imagem": image,
        "link": affiliate,
        "descricao": clean_text(row.get("description"))[:800],
        "pontuacao": make_score(row),
    }

def download_feed(url):
    fd, path = tempfile.mkstemp(prefix="shopee_feed_", suffix=".csv")
    os.close(fd)
    print("Baixando datafeed...")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Saber-e-Poder-V4/1.0"}
    )
    with urllib.request.urlopen(request, timeout=180) as response, open(path, "wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    return Path(path)

def detect_encoding(path):
    # Os feeds enviados são compatíveis com UTF-8.
    return "utf-8-sig"

def process(input_path):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    by_category = defaultdict(list)
    seen = set()
    total = 0
    accepted = 0

    with open(input_path, "r", encoding=detect_encoding(input_path), newline="", errors="replace") as f:
        reader = csv.DictReader(f)

        required = {"itemid", "title", "image_link", "product_short link"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise RuntimeError(
                "Feed incompatível. Campos ausentes: " + ", ".join(sorted(missing))
            )

        for row in reader:
            total += 1
            product = normalize(row)
            if not product:
                continue

            pid = product["id"]
            if not pid or pid in seen:
                continue

            seen.add(pid)
            by_category[product["categoria"]].append(product)
            accepted += 1

    # Ordena por pontuação e limita cada categoria.
    products = []
    for category, items in by_category.items():
        items.sort(key=lambda x: x["pontuacao"], reverse=True)
        products.extend(items[:MAX_PER_CATEGORY])

    products.sort(key=lambda x: x["pontuacao"], reverse=True)
    products = products[:MAX_PRODUCTS]

    categories = []
    counts = Counter(p["categoria"] for p in products)
    for name, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        categories.append({
            "nome": name,
            "quantidade": count,
            "slug": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        })

    output = {
        "version": 1,
        "source": "Shopee Affiliate Datafeed",
        "updated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "total_lidos": total,
        "total_aprovados": accepted,
        "total_publicados": len(products),
        "products": products,
    }

    DEFAULT_OUTPUT.write_text(
        json.dumps(output, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8"
    )

    DEFAULT_CATEGORIES.write_text(
        json.dumps(
            {
                "version": 1,
                "updated_at": output["updated_at"],
                "categories": categories,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8"
    )

    print(f"Produtos lidos:       {total}")
    print(f"Produtos válidos:     {accepted}")
    print(f"Produtos publicados:  {len(products)}")
    print(f"Categorias:           {len(categories)}")
    print(f"Gerado: {DEFAULT_OUTPUT}")
    print(f"Gerado: {DEFAULT_CATEGORIES}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        help="CSV local para teste. Se omitido, usa SHOPEE_DATAFEED_URL."
    )
    args = parser.parse_args()

    temp_path = None
    try:
        if args.input:
            input_path = Path(args.input)
            if not input_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")
        else:
            url = os.getenv("SHOPEE_DATAFEED_URL", "").strip()
            if not url:
                raise RuntimeError(
                    "Defina SHOPEE_DATAFEED_URL ou use --input arquivo.csv"
                )
            input_path = download_feed(url)
            temp_path = input_path

        process(input_path)

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()

if __name__ == "__main__":
    main()
