/**
 * Utilitário de renderização da arte final usando HTML5 Canvas API
 */

// Helper interno que contém a lógica de desenho
const renderCanvas = ({
    imagemBase64,
    detalhes,
    preco,
    formato = 'orig',
    mostrarPreco,
    mostrarParcelas,
    valoresPinos = {},
    boxes = [],
}) => {
    return new Promise((resolve, reject) => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();

        img.onload = () => {
            try {
                // 1. Definição das Dimensões do Canvas (Crop)
                let sw, sh, sx, sy; // Source width, height, x, y
                let dw, dh; // Destination width, height

                // Dimensões originais
                const ow = img.width;
                const oh = img.height;

                switch (formato) {
                    case '1:1': // Quadrado
                        const minSide = Math.min(ow, oh);
                        sw = minSide;
                        sh = minSide;
                        sx = (ow - minSide) / 2;
                        sy = (oh - minSide) / 2;
                        dw = 1080; // Padronizar saída para alta qualidade
                        dh = 1080;
                        break;

                    case 'story': // 9:16
                        // Proporção alvo: 9/16 = 0.5625
                        const targetRatioStory = 9 / 16;
                        const currentRatioStory = ow / oh;

                        if (currentRatioStory > targetRatioStory) {
                            // Imagem mais larga que o alvo: corta laterais
                            sh = oh;
                            sw = oh * targetRatioStory;
                            sy = 0;
                            sx = (ow - sw) / 2;
                        } else {
                            // Imagem mais alta que o alvo: corta topo/baixo
                            sw = ow;
                            sh = ow / targetRatioStory;
                            sx = 0;
                            sy = (oh - sh) / 2;
                        }
                        dw = 1080;
                        dh = 1920;
                        break;

                    case '4:5': // Feed Vertical
                        // Proporção alvo: 4/5 = 0.8
                        const targetRatioFeed = 4 / 5;
                        const currentRatioFeed = ow / oh;

                        if (currentRatioFeed > targetRatioFeed) {
                            sh = oh;
                            sw = oh * targetRatioFeed;
                            sy = 0;
                            sx = (ow - sw) / 2;
                        } else {
                            sw = ow;
                            sh = ow / targetRatioFeed;
                            sx = 0;
                            sy = (oh - sh) / 2;
                        }
                        dw = 1080;
                        dh = 1350;
                        break;

                    case 'orig':
                    default:
                        sw = ow;
                        sh = oh;
                        sx = 0;
                        sy = 0;
                        // Limitar tamanho máximo para não explodir memória em fotos gigantes
                        const maxSize = 2048;
                        if (ow > maxSize || oh > maxSize) {
                            const scale = Math.min(maxSize / ow, maxSize / oh);
                            dw = ow * scale;
                            dh = oh * scale;
                        } else {
                            dw = ow;
                            dh = oh;
                        }
                        break;
                }

                canvas.width = dw;
                canvas.height = dh;

                // Desenhar imagem recortada (Crop)
                // ctx.drawImage(image, sx, sy, sWidth, sHeight, dx, dy, dWidth, dHeight)
                ctx.drawImage(img, sx, sy, sw, sh, 0, 0, dw, dh);

                // Fator de escala para mapear coordenadas originais para o novo canvas
                // Importante para os pinos ficarem no lugar certo após o crop
                const scaleX = dw / sw;
                const scaleY = dh / sh;


                // 2. Identidade Visual de Luxo (Overlays)

                // Gradiente Inferior para legibilidade
                const gradientHeight = dh * 0.35; // 35% da altura
                const gradient = ctx.createLinearGradient(0, dh - gradientHeight, 0, dh);
                gradient.addColorStop(0, 'rgba(0, 0, 0, 0)');
                gradient.addColorStop(1, 'rgba(0, 0, 0, 0.85)');

                ctx.fillStyle = gradient;
                ctx.fillRect(0, dh - gradientHeight, dw, gradientHeight);


                // 3. Renderização de Conteúdo

                const hasPinos = Object.keys(valoresPinos).length > 0;

                if (hasPinos) {
                    // --- MODO PINOS (MÚLTIPLOS PREÇOS) ---

                    boxes.forEach((box, index) => {
                        const valor = valoresPinos[index]; // Pega o valor digitado para este box
                        if (!valor) return; // Se usuário não digitou nada, pula

                        // Coordenadas originais do box
                        // box = [x, y, w, h]
                        // Precisamos converter para o sistema de coordenadas do canvas recortado (dw, dh)

                        // 1. Ajustar origem (subtrair o crop start)
                        let boxX = box[0] - sx;
                        let boxY = box[1] - sy;

                        // 2. Aplicar escala
                        boxX *= scaleX;
                        boxY *= scaleY;
                        const boxW = box[2] * scaleX;
                        const boxH = box[3] * scaleY;

                        // Verificar se o pino ainda está dentro da área visível após o crop
                        if (boxX + boxW < 0 || boxY + boxH < 0 || boxX > dw || boxY > dh) {
                            return; // Box foi cortado fora
                        }

                        // Desenhar Pílula de Preço
                        const fontSize = Math.max(14, dw * 0.025); // Responsivo
                        ctx.font = `600 ${fontSize}px Inter, sans-serif`;
                        const paddingX = fontSize * 1.2;
                        const paddingY = fontSize * 0.8;
                        const textMetrics = ctx.measureText(valor);
                        const textWidth = textMetrics.width;

                        const pillW = textWidth + (paddingX * 2);
                        const pillH = fontSize + (paddingY * 2);

                        // Centralizar pílula sobre a área do box antigo
                        const pillX = boxX + (boxW / 2) - (pillW / 2);
                        const pillY = boxY + (boxH / 2) - (pillH / 2);

                        // Desenhar retângulo arredondado (Pílula)
                        ctx.fillStyle = 'rgba(34, 29, 16, 0.9)'; // Fundo escuro (background-dark)
                        ctx.strokeStyle = '#ecb613'; // Borda Dourada (primary)
                        ctx.lineWidth = 2;

                        roundRect(ctx, pillX, pillY, pillW, pillH, pillH / 2); // Pill shape
                        ctx.fill();
                        ctx.stroke();

                        // Texto do Valor
                        ctx.fillStyle = '#ffffff';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        // Sombra suave no texto
                        ctx.shadowColor = 'rgba(0,0,0,0.5)';
                        ctx.shadowBlur = 4;
                        ctx.shadowOffsetX = 0;
                        ctx.shadowOffsetY = 1;

                        ctx.fillText(valor, pillX + (pillW / 2), pillY + (pillH / 2));

                        // Reset shadow
                        ctx.shadowColor = 'transparent';
                    });

                } else {
                    // --- MODO SINGLE CARD (VOGUE STYLE) ---
                    // Box flutuante contendo Nome e Preço

                    if (detalhes || (mostrarPreco && preco)) {
                        // Configuração de Fontes
                        const nameFontSize = dw * 0.035; // 3.5% da largura (Nome menor e elegante)
                        const priceFontSize = dw * 0.06; // 6.0% da largura (Preço maior e bold)
                        const fontName = `500 ${nameFontSize}px Inter, sans-serif`;
                        const fontPrice = `700 ${priceFontSize}px Inter, sans-serif`;

                        // Medições
                        ctx.font = fontName;
                        const nameMetrics = detalhes ? ctx.measureText(detalhes) : { width: 0 };

                        ctx.font = fontPrice;
                        const priceText = (mostrarPreco && preco) ? preco : "";
                        const priceMetrics = priceText ? ctx.measureText(priceText) : { width: 0 };

                        // Largura do Box = Maior Texto + Padding Generoso
                        const maxTextWidth = Math.max(nameMetrics.width, priceMetrics.width);
                        const paddingX = dw * 0.05; // Padding lateral
                        const paddingY = dw * 0.035; // Padding vertical
                        const gap = dw * 0.015; // Espaço vertical entre nome e preço

                        const boxW = maxTextWidth + (paddingX * 2);
                        const boxH = (detalhes ? nameFontSize : 0) +
                            (priceText ? priceFontSize : 0) +
                            (detalhes && priceText ? gap : 0) +
                            (paddingY * 2);

                        // Posição: Centralizado Horizontal, Inferior Vertical (com margem)
                        const marginBottom = dh * 0.12; // 12% da altura como margem inferior
                        const boxX = (dw - boxW) / 2;
                        const boxY = dh - marginBottom - boxH;

                        // Desenhar Box (Glassmorphism White)
                        ctx.save();
                        // Sombra suave para destacar
                        ctx.shadowColor = "rgba(0, 0, 0, 0.25)";
                        ctx.shadowBlur = 25;
                        ctx.shadowOffsetY = 8;

                        ctx.fillStyle = "rgba(255, 255, 255, 0.95)"; // Branco quase sólido

                        ctx.beginPath();
                        roundRect(ctx, boxX, boxY, boxW, boxH, boxH * 0.15); // Cantos levemente arredondados
                        ctx.fill();
                        ctx.restore();

                        // Desenhar Textos
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'top';
                        ctx.fillStyle = '#111827'; // Dark Gray (Quase preto)

                        let currentY = boxY + paddingY;

                        // 1. Nome do Produto (Topo)
                        if (detalhes) {
                            ctx.font = fontName;
                            // centralizado no box
                            ctx.fillText(detalhes, boxX + (boxW / 2), currentY);
                            currentY += nameFontSize + gap;
                        }

                        // 2. Preço (Baixo)
                        if (priceText) {
                            ctx.font = fontPrice;
                            // Ajuste fino para vertical alignment do preço
                            ctx.fillText(priceText, boxX + (boxW / 2), currentY);
                        }
                    }
                }

                resolve(canvas);

            } catch (err) {
                reject(err);
            }
        };

        img.onerror = (err) => reject(err);
        // Importante: allow canvas export
        img.crossOrigin = "anonymous";
        img.src = `data:image/png;base64,${imagemBase64}`;
    });
};

// Gera fundo limpo (foto + gradiente artístico, SEM textos/glassmorphism).
// Fonte da verdade do background no Stage Konva — T-DND-006.
export const gerarFundoLimpo = async (imagemBase64, formato = 'orig') => {
    const canvas = await renderCanvas({
        imagemBase64,
        formato,
        detalhes: '',
        preco: '',
        mostrarPreco: false,
        mostrarParcelas: false,
        valoresPinos: {},
        boxes: [],
    });
    return canvas.toDataURL('image/jpeg', 0.85);
};

// Salva ou compartilha um dataURL como JPEG.
// Em plataforma nativa Capacitor: usa Filesystem + Share.
// Em browser ou fallback: usa link <a download>.
export async function salvarDataURL(dataURL, filename) {
    if (typeof window !== 'undefined' && window.Capacitor?.isNativePlatform?.()) {
        try {
            const cap = (pkg) => `@capacitor/${pkg}`;
            const { Filesystem, Directory } = await import(cap('filesystem'));
            const { Share } = await import(cap('share'));
            const base64Data = dataURL.split(',')[1];
            const saved = await Filesystem.writeFile({
                path: filename,
                data: base64Data,
                directory: Directory.Cache,
            });
            await Share.share({
                title: 'Sua Arte Premium',
                url: saved.uri,
                dialogTitle: 'Salvar ou compartilhar',
            });
            return;
        } catch (err) {
            console.warn('Capacitor share falhou, fallback DOM:', err);
            // Fall through para DOM
        }
    }
    // Browser ou fallback: DOM <a download>
    const link = document.createElement('a');
    link.href = dataURL;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// @deprecated — T-DND-006: use gerarFundoLimpo no preview e stage.toDataURL no export.
// Mantido para o fluxo de pinos (ModalPinos via WorkspacePage).
export const gerarArteDataURL = async (config) => {
    const canvas = await renderCanvas(config);
    return canvas.toDataURL('image/jpeg', 0.85); // Preview um pouco mais leve
};

// @deprecated — T-DND-006: use salvarDataURL com o dataURL do Stage Konva.
// Mantido para o fluxo de pinos (ModalPinos via WorkspacePage).
export const gerarEBaixarArte = async (config) => {
    const canvas = await renderCanvas(config);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.95);

    // Criar link temporário
    const link = document.createElement('a');
    link.href = dataUrl;
    link.download = `precificas-luxo-${Date.now()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    return true;
};


// Helper para desenhar retângulos arredondados no Canvas
function roundRect(ctx, x, y, width, height, radius) {
    if (typeof radius === 'undefined') {
        radius = 5;
    }
    if (typeof radius === 'number') {
        radius = { tl: radius, tr: radius, br: radius, bl: radius };
    } else {
        var defaultRadius = { tl: 0, tr: 0, br: 0, bl: 0 };
        for (var side in defaultRadius) {
            radius[side] = radius[side] || defaultRadius[side];
        }
    }
    ctx.beginPath();
    ctx.moveTo(x + radius.tl, y);
    ctx.lineTo(x + width - radius.tr, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius.tr);
    ctx.lineTo(x + width, y + height - radius.br);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius.br, y + height);
    ctx.lineTo(x + radius.bl, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius.bl);
    ctx.lineTo(x, y + radius.tl);
    ctx.quadraticCurveTo(x, y, x + radius.tl, y);
    ctx.closePath();
}
