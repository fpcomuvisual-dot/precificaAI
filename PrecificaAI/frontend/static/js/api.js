/**
 * PrecificaAI — Módulo de comunicação com o Backend.
 * O front importa este arquivo e usa as funções para falar com a API.
 */

const API_BASE = window.location.origin; // Mesmo servidor (FastAPI serve tudo)

// ============================================================
// PROCESSAR IMAGEM INDIVIDUAL
// ============================================================
async function processarImagem(imageBase64, texto, config = {}) {
    const payload = {
        image: imageBase64,
        texto: texto,
        config: {
            formato: config.formato || "original",
            paleta: config.paleta || "classico",
            modo_preco: config.modo_preco || "padrao",
        }
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
    // Retorna: { status, url_resultado, dados_extraidos, tempo_processamento_ms }
}


// ============================================================
// PROCESSAR BATCH
// ============================================================
async function processarBatch(itens, config = {}) {
    // itens = [{ image: base64, texto: "colar ouro 89" }, ...]
    const payload = {
        itens: itens,
        config: {
            formato: config.formato || "original",
            paleta: config.paleta || "classico",
            modo_preco: config.modo_preco || "padrao",
        }
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
    // Retorna: { status, resultados: [...], resumo: { total, sucesso, falha } }
}


// ============================================================
// RENDERIZAR COM DADOS CONFIRMADOS (Pós Card de Confirmação)
// ============================================================
async function renderizarConfirmado(imageBase64, dadosConfirmados, config = {}) {
    const payload = {
        image: imageBase64,
        dados_confirmados: dadosConfirmados,
        config: {
            formato: config.formato || "original",
            paleta: config.paleta || "classico",
            modo_preco: config.modo_preco || "padrao",
        }
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


// ============================================================
// HELPERS
// ============================================================

/**
 * Converte arquivo (File) em base64.
 * Chamado pelo input de upload antes de enviar ao backend.
 */
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result); // Inclui "data:image/jpeg;base64,..."
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

/**
 * Comprime imagem no cliente antes de enviar.
 * Redimensiona para máx 3000px no lado maior.
 */
function comprimirImagem(file, maxDimension = 3000, quality = 0.85) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            let { width, height } = img;

            // Só redimensiona se necessário
            if (width > maxDimension || height > maxDimension) {
                if (width > height) {
                    height = Math.round((height * maxDimension) / width);
                    width = maxDimension;
                } else {
                    width = Math.round((width * maxDimension) / height);
                    height = maxDimension;
                }
            }

            const canvas = document.createElement("canvas");
            canvas.width = width;
            canvas.height = height;

            const ctx = canvas.getContext("2d");
            ctx.drawImage(img, 0, 0, width, height);

            canvas.toBlob(
                (blob) => resolve(blob),
                "image/jpeg",
                quality
            );
        };
        img.src = URL.createObjectURL(file);
    });
}

/**
 * Health check — verifica se o backend está online.
 */
async function healthCheck() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        return await response.json();
    } catch {
        return { status: "offline" };
    }
}
