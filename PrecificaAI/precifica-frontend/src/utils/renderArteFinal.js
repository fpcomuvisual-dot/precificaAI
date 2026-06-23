/**
 * Utilitário de renderização da arte final usando HTML5 Canvas API
 */
import { Capacitor } from '@capacitor/core';
import { Filesystem, Directory } from '@capacitor/filesystem';
import { Share } from '@capacitor/share';

// Helper interno que contém a lógica de desenho
const renderCanvas = ({
    imagemBase64,
    detalhes,
    preco,
    formato = 'orig',
    mostrarPreco,
    mostrarParcelas,
    parcelas = '',
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
                    // --- MODO SINGLE CARD — etiqueta canto inferior-direito ---
                    // Safe zone: WhatsApp/Instagram preview 4:5 = 1080×1350 (y≤1350).
                    // Âncora em y=1150 (60% de 1920) — visível em qualquer preview.

                    const priceText = (mostrarPreco && preco) ? preco : '';
                    const parcelasText = (mostrarParcelas && parcelas) ? parcelas : '';

                    if (detalhes || priceText) {
                        const anchorX = 780;   // right edge (72% de dw=1080)
                        const anchorY = 1150;  // topo do bloco (60% de dh=1920)

                        // 1. Nome — right-aligned, branco com sombra forte
                        if (detalhes) {
                            ctx.font = '500 28px Inter, sans-serif';
                            ctx.textAlign = 'right';
                            ctx.textBaseline = 'top';
                            ctx.fillStyle = '#FFFFFF';
                            ctx.shadowColor = 'rgba(0,0,0,0.75)';
                            ctx.shadowBlur = 6;
                            ctx.shadowOffsetX = 0;
                            ctx.shadowOffsetY = 2;
                            ctx.fillText(detalhes, anchorX, anchorY);
                            ctx.shadowColor = 'transparent';
                            ctx.shadowBlur = 0;
                            ctx.shadowOffsetY = 0;
                        }

                        // 2. Pílula branca para preço — right-aligned em anchorX
                        if (priceText) {
                            ctx.font = '700 36px Inter, sans-serif';
                            const pillPadX = 40;
                            const pillH = 55;
                            const pillW = ctx.measureText(priceText).width + pillPadX * 2;
                            const pillX = anchorX - pillW;  // right edge = anchorX
                            const pillY = anchorY + 35;      // y≈1185

                            ctx.save();
                            ctx.shadowColor = 'rgba(0,0,0,0.2)';
                            ctx.shadowBlur = 10;
                            ctx.shadowOffsetY = 3;
                            ctx.fillStyle = '#FFFFFF';
                            roundRect(ctx, pillX, pillY, pillW, pillH, pillH / 2);
                            ctx.fill();
                            ctx.restore();

                            ctx.font = '700 36px Inter, sans-serif';
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            ctx.fillStyle = '#1A1611';
                            ctx.fillText(priceText, pillX + pillW / 2, pillY + pillH / 2);
                        }

                        // 3. Parcelas — right-aligned, branco semitransparente
                        if (parcelasText) {
                            ctx.font = '400 20px Inter, sans-serif';
                            ctx.textAlign = 'right';
                            ctx.textBaseline = 'top';
                            ctx.fillStyle = 'rgba(255,255,255,0.8)';
                            ctx.fillText(parcelasText, anchorX, 1250);
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
    if (Capacitor.isNativePlatform()) {
        try {
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
// TODO: T-RENDER-001 — unificar renderização batch (Canvas) com single-item (Konva).
export const gerarArteDataURL = async (config) => {
    const canvas = await renderCanvas(config);
    return canvas.toDataURL('image/jpeg', 0.85); // Preview um pouco mais leve
};

// @deprecated — T-DND-006: use salvarDataURL com o dataURL do Stage Konva.
// Mantido para o fluxo de pinos (ModalPinos via WorkspacePage).
export const gerarEBaixarArte = async (config) => {
    const canvas = await renderCanvas(config);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
    const nomeArquivo = `precificas-luxo-${Date.now()}.jpg`;
    // Reusa salvarDataURL (Capacitor Filesystem+Share em nativo, <a download>
    // em browser) em vez de duplicar a lógica — merge main / T-DND-006.
    await salvarDataURL(dataUrl, nomeArquivo);
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
