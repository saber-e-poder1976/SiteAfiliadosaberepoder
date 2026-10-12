/* ==========================================================
   SABER É PODER RECOMENDA — V5.20 EXIBIÇÃO CORRIGIDA
   ✅ Contador funcionando
   ✅ Cards aparecendo na tela
========================================================== */
"use strict";
const $ = (seletor) => document.querySelector(seletor);
const $$ = (seletor) => document.querySelectorAll(seletor);
let categorias = [];
let todosProdutos = [];
let produtosFiltrados = [];
let categoriaAtiva = "todos";
// 🔑 SLUGS EXATOS do JSON
const SLUGS = {
    "todos": [],
    "casa-e-organizacao": ["Casa e Organização"],
    "moda-e-acessorios": ["Moda e Acessórios"],
    "outros": ["Outros"],
    "tecnologia": ["Tecnologia"],
    "bebe-e-infantil": ["Bebê e Infantil"],
    "beleza-e-skincare": ["Beleza e Skincare"],
    "esportes-e-lazer": ["Esportes e Lazer"],
    "saude-e-bem-estar": ["Saúde e Bem-estar"],
    "pets": ["Pets"],
    "hobbies-e-colecoes": ["Hobbies e Coleções"],
    "alimentos-e-bebidas": ["Alimentos e Bebidas"],
    "livros-e-papelaria": ["Livros e Papelaria"]
};
function normalizar(texto) {
    if (!texto) return "";
    return String(texto)
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim();
}
document.addEventListener("DOMContentLoaded", async () => {
    console.log("🚀 Página carregada — iniciando...");
    await carregarTudo();
    vincularBotoes();
    aplicarFiltro();
});
async function carregarTudo() {
    const caminhos = ["./", "./data/"];
    let carregou = false;
    for (const caminho of caminhos) {
        try {
            console.log(`🔍 Buscando em: ${caminho}`);
            
            const respCat = await fetch(`${caminho}categorias.json`);
            if (!respCat.ok) continue;
            const dadosCat = await respCat.json();
            categorias = dadosCat.categories || [];
            console.log(`✅ ${categorias.length} categorias carregadas`);
            const respProd = await fetch(`${caminho}produtos.json`);
            if (!respProd.ok) continue;
            const dadosProd = await respProd.json();
            todosProdutos = dadosProd.products || [];
            produtosFiltrados = [...todosProdutos];
            console.log(`✅ ${todosProdutos.length} produtos carregados`);
            carregou = true;
            break;
        } catch (erro) {
            console.log(`❌ Falha em ${caminho}:`, erro.message);
        }
    }
    if (!carregou) {
        mostrarAviso("Não encontrei os arquivos JSON. Verifique se estão na pasta correta.");
        return;
    }
    renderizarProdutos();
    atualizarContador();
}
function vincularBotoes() {
    $$("[data-categoria]").forEach(botao => {
        botao.addEventListener("click", (e) => {
            e.preventDefault();
            categoriaAtiva = botao.dataset.categoria;
            $$("[data-categoria]").forEach(b => b.classList.remove("active"));
            botao.classList.add("active");
            aplicarFiltro();
            rolarAteSecao();
        });
    });
}
function aplicarFiltro() {
    console.log(`🔍 Filtrando: ${categoriaAtiva}`);
    
    if (categoriaAtiva === "todos") {
        produtosFiltrados = [...todosProdutos];
    } else {
        const nomesEsperados = SLUGS[categoriaAtiva] || [categoriaAtiva];
        
        produtosFiltrados = todosProdutos.filter(produto => {
            const catProd = normalizar(produto.categoria || "");
            return nomesEsperados.some(nome => 
                catProd === normalizar(nome) || catProd.includes(normalizar(nome))
            );
        });
    }
    console.log(`✅ ${produtosFiltrados.length} produtos após filtro`);
    renderizarProdutos();
    atualizarContador();
}
function renderizarProdutos() {
    const container = document.querySelector(".produtos-grid");
    if (!container) {
        console.log("❌ Container .produtos-grid NÃO encontrado no HTML!");
        return;
    }
    container.innerHTML = "";
    if (produtosFiltrados.length === 0) {
        container.innerHTML = `<p style="grid-column:1/-1;text-align:center;padding:3rem;color:#666;">Nenhum produto encontrado 😔</p>`;
        return;
    }
    produtosFiltrados.forEach(produto => {
        const desconto = produto.desconto || 0;
        const card = document.createElement("div");
        card.className = "product-card";
        card.innerHTML = `
            ${desconto > 0 ? `<span class="badge-desconto">-${desconto}%</span>` : ""}
            <img src="${produto.imagem}" alt="${produto.nome}" loading="lazy" 
                 onerror="this.src='img/sem-imagem.png'">
            <h3>${produto.nome}</h3>
            <div class="precos">
                ${produto.preco_original ? `<span class="preco-original">De R$ ${produto.preco_original}</span>` : ""}
                <span class="preco-atual">Por R$ ${produto.preco}</span>
            </div>
            <a href="${produto.link}" target="_blank" rel="nofollow sponsored noopener" class="btn-primary">Ver Oferta</a>
        `;
        container.appendChild(card);
    });
    console.log(`✅ ${produtosFiltrados.length} cards renderizados`);
}
function atualizarContador() {
    const el = document.querySelector(".contador-resultados");
    if (!el) return;
    const cat = categorias.find(c => c.slug === categoriaAtiva);
    const nome = cat?.nome || "Todos os produtos";
    const qtd = cat?.quantidade ?? produtosFiltrados.length;
    el.textContent = `${nome}: ${qtd} produto${qtd !== 1 ? "s" : ""}`;
}
function rolarAteSecao() {
    const alvo = document.getElementById("produtos");
    if (alvo) {
        setTimeout(() => {
            alvo.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 100);
    }
}
function mostrarAviso(texto) {
    const container = document.querySelector(".produtos-grid");
    if (container) {
        container.innerHTML = `<p style="grid-column:1/-1;text-align:center;padding:3rem;color:#d32f2f;">⚠️ ${texto}</p>`;
    }
}