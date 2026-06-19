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

export async function processarTexto(texto, apiBase) {
    const base = apiBase || getApiBase();

    const response = await fetch(`${base}/api/processar-texto`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto }),
    });

    if (!response.ok) {
        let motivo = "";
        try {
            const erro = await response.json();
            motivo = erro.motivo || erro.message || "";
        } catch {
            /* corpo não-JSON */
        }
        if (response.status === 422) {
            throw new Error(
                "A IA não conseguiu entender a descrição. Revise o texto e tente de novo."
            );
        }
        throw new Error(motivo || "Erro ao processar o texto. Tente novamente.");
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
