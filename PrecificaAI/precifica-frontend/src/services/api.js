const getApiBase = () => {
    return localStorage.getItem('API_BASE') || 'https://precifica-api-356056496893.us-central1.run.app';
};

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

    const response = await fetch(`${getApiBase()}/api/processar`, {
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

    const response = await fetch(`${getApiBase()}/api/processar/batch`, {
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

    const response = await fetch(`${getApiBase()}/api/renderizar`, {
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
        const response = await fetch(`${getApiBase()}/api/health`);
        return await response.json();
    } catch {
        return { status: "offline" };
    }
}
