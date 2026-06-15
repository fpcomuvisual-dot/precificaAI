// String vazia = paths relativos = usa o proxy do Vite em dev
// e o mesmo domínio em produção.
const API_BASE = "";

export async function processarImagem(imageBase64, texto, config = {}) {
    const payload = {
        image: imageBase64,
        texto: texto,
        config: {
            formato: config.formato || "original",
            paleta: config.paleta || "classico",
            modo_preco: config.modo_preco || "padrao",
        },
    };

    const response = await fetch(`${API_BASE}/api/processar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Erro ao processar imagem");
    }

    return await response.json();
}

export async function processarBatch(itens, config = {}) {
    const payload = {
        itens: itens,
        config: {
            formato: config.formato || "original",
            paleta: config.paleta || "classico",
            modo_preco: config.modo_preco || "padrao",
        },
    };

    const response = await fetch(`${API_BASE}/api/processar/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Erro ao processar lote");
    }

    return await response.json();
}

export async function renderizarConfirmado(
    imageBase64,
    dadosConfirmados,
    config = {}
) {
    const payload = {
        image: imageBase64,
        dados_confirmados: dadosConfirmados,
        config: {
            formato: config.formato || "original",
            paleta: config.paleta || "classico",
            modo_preco: config.modo_preco || "padrao",
        },
    };

    const response = await fetch(`${API_BASE}/api/renderizar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Erro ao renderizar");
    }

    return await response.json();
}

export async function healthCheck() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        return await response.json();
    } catch {
        return { status: "offline" };
    }
}
