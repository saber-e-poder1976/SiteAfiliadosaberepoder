/* ==========================================================
   SABER É PODER RECOMENDA — V5.22 COM PESQUISA INTEGRADA
   ✅ Carrega categorias e produtos do JSON
   ✅ Filtro por categoria clicável
   ✅ 🔍 Pesquisa em tempo real (nome, descrição, categoria)
   ✅ Combina categoria + pesquisa
   ✅ Contador atualizado
   ✅ Rolagem suave
========================================================== */
"use strict";

const $ = (seletor) => document.querySelector(seletor);
const $$ = (seletor) => document.querySelectorAll(seletor);

let categorias = [];
let todosProdutos = [];
let produtosFiltrados = [];
let categoriaAtiva = "todos";
let termoPesquisa = "";

// SLUGS correspondentes ao JSON
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
    vincularBotoesCategorias();
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

function vincularBotoesCategorias() {
    $$(".menu-categorias span[data-categoria]").forEach(botao => {
        botao.addEventListener("click", () => {
            categoriaAtiva = botao.dataset.categoria;
            termoPesquisa = ""; // Limpa pesquisa ao trocar categoria
            $$(".menu-categorias span").forEach(b => b.classList.remove("active"));
            botao.classList.add("active");
            aplicarFiltro();
            rolarAteSecao();
            // Limpa o campo de pesquisa na tela
            const campo = $("#pesquisa-produtos");
            if (campo) campo.value = "";
        });
    });
}

// Chamada pelo HTML
function aplicarFiltroPorCategoria(slug) {
    categoriaAtiva = slug;
    termoPesquisa = "";
    aplicarFiltro();
    rolarAteSecao();
}

// Chamada pelo HTML
function buscarProdutos(termo) {
    termoPesquisa = normalizar(termo);
    aplicarFiltro();
}

function aplicarFiltro() {
    console.log(`🔍 Filtro | Categoria: ${categoriaAtiva} | Busca: "${termoPesquisa}"`);
    
    let resultado = [...todosProdutos];
    
    // Filtro por categoria
    if (categoriaAtiva !== "todos") {
        const nomesEsperados = SLUGS[categoriaAtiva] || [categoriaAtiva];
        resultado = resultado.filter(produto => {
            const catProd = normalizar(produto.categoria || "");
            return nomesEsperados.some(nome => 
                catProd === normalizar(nome) || catProd.includes(normalizar(nome))
            );
        });
    }
    
    // Filtro por pesquisa
    if (termoPesquisa.length > 0) {
        resultado = resultado.filter(produto => {
            const nome = normalizar(produto.nome || "");
            const desc = normalizar(produto.descricao || "");
            const cat = normalizar(produto.categoria || "");
            return nome.includes(termoPesquisa) || 
                   desc.includes(termoPesquisa) || 
                   cat.includes(termoPesquisa);
        });
    }
    
    produtosFiltrados = resultado;
    console.log(`✅ ${produtosFiltrados.length} produtos encontrados`);
    
    renderizarProdutos();
    atualizarContador();
}

function renderizarProdutos() {
    const container = $(".produtos-grid");
    if (!container) {
        console.log("❌ Container .produtos-grid NÃO encontrado!");
        return;
    }
    container.innerHTML = "";
    
    if (produtosFiltrados.length === 0) {
        container.innerHTML = `<p style="grid-column:1/-1;text-align:center;padding:3rem;color:#666;">
            Nenhum produto encontrado 😔<br>
            Tente pesquisar por outro termo ou escolha outra categoria
        </p>`;
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
}

function atualizarContador() {
    const el = $("#contadorResultados");
    if (!el) return;
    
    let texto = "";
    if (termoPesquisa.length > 0) {
        texto = `Pesquisa por "${termoPesquisa}": ${produtosFiltrados.length} resultado${produtosFiltrados.length !== 1 ? "s" : ""}`;
    } else {
        const cat = categorias.find(c => c.slug === categoriaAtiva);
        const nome = cat?.nome || "Todos os produtos";
        const qtd = cat?.quantidade ?? produtosFiltrados.length;
        texto = `${nome}: ${qtd} produto${qtd !== 1 ? "s" : ""}`;
    }
    el.textContent = texto;
}

function rolarAteSecao() {
    const alvo = $("#produtos");
    if (alvo) {
        setTimeout(() => {
            alvo.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 100);
    }
}

function mostrarAviso(texto) {
    const container = $(".produtos-grid");
    if (container) {
        container.innerHTML = `<p style="grid-column:1/-1;text-align:center;padding:3rem;color:#d32f2f;">⚠️ ${texto}</p>`;
    }
}