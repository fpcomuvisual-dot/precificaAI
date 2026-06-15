import numpy as np
from PIL import Image, ImageDraw


# ============================================================
# MARGENS INVISÍVEIS (SAFE ZONES)
# ============================================================
#
# Pense como as guias ciano/magenta do Photoshop:
#
#  ┌──────────────────────────────────┐
#  │  ╔═══ MARGEM TOPO (8%) ═══════╗ │
#  │  ║                             ║ │
#  │  ║  SAFE ZONE (conteúdo aqui)  ║ │
#  │  ║                             ║ │
#  │  ╚═══ MARGEM BASE (8%) ═══════╝ │
#  │← 6% →│                   │← 6% →│
#  └──────────────────────────────────┘
#
# Instagram recomenda: 5% de margem em todos os lados
# Nós usamos 6% lateral e 8% topo/base (mais respiro vertical)

MARGENS = {
    "original": {
        "topo": 0.05,      # 5% margem topo (Padrão)
        "base": 0.05,      # 5% margem base
        "esquerda": 0.05,  # 5% margem esquerda
        "direita": 0.05,   # 5% margem direita
    },
    "feed_quadrado": {
        "topo": 0.05,
        "base": 0.05,
        "esquerda": 0.05,
        "direita": 0.05,
    },
    "feed_retrato": {
        "topo": 0.05,
        "base": 0.05,
        "esquerda": 0.05,
        "direita": 0.05,
    },
    "stories": {
        "topo": 0.08,       # Stories ainda precisa de um pouco mais (UI do app)
        "base": 0.08,
        "esquerda": 0.03,
        "direita": 0.03,
    },
}


def get_safe_zone(w, h, formato="original"):
    """
    Retorna as coordenadas da safe zone (onde o texto PODE ficar).
    Tudo fora disso é margem invisível — o texto nunca toca.
    """
    m = MARGENS.get(formato, MARGENS["original"])
    
    x1 = int(w * m["esquerda"])
    y1 = int(h * m["topo"])
    x2 = int(w * (1 - m["direita"]))
    y2 = int(h * (1 - m["base"]))
    
    return (x1, y1, x2, y2)


# ============================================================
# DETECÇÃO DE PELE (RÁPIDA, VETORIZADA)
# ============================================================

def detectar_pele_rapido(image, target_size=None):
    """
    Detecta tons de pele com numpy vetorizado.
    <20ms para 1024x1024. Sem loops Python.
    """
    if target_size:
        image = image.resize(target_size, Image.LANCZOS)
    
    img = np.array(image.convert('RGB')).astype(np.float32)
    r, g, b = img[:,:,0], img[:,:,1], img[:,:,2]
    
    # Detecção de pele multi-regra (funciona com todas as tonalidades)
    mask = (
        (r > 60) & (g > 40) & (b > 20) &
        (r > g) & (r > b) &
        (np.abs(r - g) > 10) &
        ((r - b) > 15)
    )
    
    # Regra adicional para peles mais escuras
    mask_escura = (
        (r > 40) & (g > 25) & (b > 15) &
        (r > g) & (r > b) &
        ((r - b) > 10)
    )
    
    mask_final = mask | mask_escura
    
    # Limpeza morfológica (sem scipy — pure numpy)
    # Erosão simples via slicing
    eroded = mask_final[1:-1, 1:-1] & mask_final[:-2, 1:-1] & mask_final[2:, 1:-1] & \
             mask_final[1:-1, :-2] & mask_final[1:-1, 2:]
    
    # Pad de volta ao tamanho original
    result = np.zeros_like(mask_final, dtype=np.uint8)
    result[1:-1, 1:-1] = eroded.astype(np.uint8)
    
    return result


# ============================================================
# MÁSCARA COMBINADA
# ============================================================

def criar_mask_proibida(image, mask_produto):
    """
    Combina: produto (Rembg) + pele = tudo que é PROIBIDO para texto.
    """
    h_mask, w_mask = mask_produto.shape
    img_resized = image.resize((w_mask, h_mask), Image.LANCZOS)
    
    mask_pele = detectar_pele_rapido(img_resized)
    
    return np.maximum(mask_produto, mask_pele)


# ============================================================
# CANDIDATOS (COMPOSIÇÃO PROFISSIONAL)
# ============================================================

def gerar_candidatos(w, h, safe_zone, formato_offset=None):
    """
    Gera zonas candidatas DENTRO da safe zone.
    Baseado em regra dos terços e golden ratio.
    
    Todos os candidatos respeitam as margens invisíveis.
    """
    sx1, sy1, sx2, sy2 = safe_zone
    sw = sx2 - sx1  # Largura útil
    sh = sy2 - sy1  # Altura útil
    
    altura_texto = int(sh * 0.20)  # 20% da altura útil para o bloco de texto
    
    candidatos = []
    
    # -------------------------------------------------------
    # 1. TERÇO INFERIOR (melhor para varejo — produto em cima, texto embaixo)
    # -------------------------------------------------------
    ti_y1 = sy1 + int(sh * 0.70)   # Começa em 70% da safe zone
    ti_y2 = min(ti_y1 + altura_texto, sy2)
    candidatos.append({
        'rect': (sx1, ti_y1, sx2, ti_y2),
        'nome': 'terco_inferior',
        'bonus': 35,
    })
    
    # -------------------------------------------------------
    # 2. GOLDEN RATIO INFERIOR (61.8%)
    # -------------------------------------------------------
    gr_y1 = sy1 + int(sh * 0.618)
    gr_y2 = min(gr_y1 + altura_texto, sy2)
    candidatos.append({
        'rect': (sx1, gr_y1, sx2, gr_y2),
        'nome': 'golden_ratio',
        'bonus': 30,
    })
    
    # -------------------------------------------------------
    # 3. TERÇO SUPERIOR (bom quando produto está embaixo)
    # -------------------------------------------------------
    ts_y1 = sy1
    ts_y2 = min(sy1 + altura_texto, sy1 + int(sh * 0.30))
    candidatos.append({
        'rect': (sx1, ts_y1, sx2, ts_y2),
        'nome': 'terco_superior',
        'bonus': 20,
    })
    
    # -------------------------------------------------------
    # 4. LATERAL ESQUERDA + TERÇO INFERIOR
    #    (quando produto/modelo está à direita)
    # -------------------------------------------------------
    candidatos.append({
        'rect': (sx1, ti_y1, sx1 + int(sw * 0.50), ti_y2),
        'nome': 'esquerda_inferior',
        'bonus': 25,
    })
    
    # -------------------------------------------------------
    # 5. LATERAL DIREITA + TERÇO INFERIOR
    #    (quando produto/modelo está à esquerda)
    # -------------------------------------------------------
    candidatos.append({
        'rect': (sx1 + int(sw * 0.50), ti_y1, sx2, ti_y2),
        'nome': 'direita_inferior',
        'bonus': 25,
    })
    
    # -------------------------------------------------------
    # 6. LATERAL ESQUERDA + TERÇO SUPERIOR
    # -------------------------------------------------------
    candidatos.append({
        'rect': (sx1, ts_y1, sx1 + int(sw * 0.50), ts_y2),
        'nome': 'esquerda_superior',
        'bonus': 15,
    })
    
    # -------------------------------------------------------
    # 7. CENTRO INFERIOR (safe bottom)
    # -------------------------------------------------------
    sb_y1 = sy2 - altura_texto
    candidatos.append({
        'rect': (sx1, sb_y1, sx2, sy2),
        'nome': 'safe_bottom',
        'bonus': 10,
    })
    
    # -------------------------------------------------------
    # 8. STORIES: zonas fora da foto central
    # -------------------------------------------------------
    if formato_offset and formato_offset[1] > 100:
        off_x, off_y, off_w, off_h = formato_offset
        
        if off_y > sy1 + 100:
            candidatos.append({
                'rect': (sx1, sy1, sx2, off_y - 20),
                'nome': 'stories_topo',
                'bonus': 30,
            })
        
        base_y = off_y + off_h + 20
        if base_y < sy2 - 50:
            candidatos.append({
                'rect': (sx1, base_y, sx2, sy2),
                'nome': 'stories_base',
                'bonus': 30,
            })
    
    return candidatos


# ============================================================
# SCORING
# ============================================================

def pontuar_candidato(rect, mask_proibida, bonus, w, h):
    """
    Score = limpeza (50) + composição (35) + área (15) - penalidades
    """
    x1, y1, x2, y2 = rect
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(w, int(x2)), min(h, int(y2))
    
    if x2 <= x1 or y2 <= y1:
        return -9999
    
    crop = mask_proibida[y1:y2, x1:x2]
    total = crop.size
    if total == 0:
        return -9999
    
    livres = np.sum(crop == 0)
    pct_livre = livres / total
    
    # Limpeza (0-50)
    score = pct_livre * 50
    
    # Composição (0-35)
    score += bonus
    
    # Área útil (0-15)
    area_pct = min(((x2-x1) * (y2-y1)) / (w * h), 0.20) / 0.20
    score += area_pct * 15
    
    # Penalidade PROGRESSIVA por ocupação
    if pct_livre < 0.60:
        score -= 15
    if pct_livre < 0.40:
        score -= 25
    if pct_livre < 0.25:
        score -= 40
    
    return score


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def encontrar_melhor_posicao_v3(image, mask_produto, w, h,
                                 padding_info, formato="original",
                                 formato_offset=None):
    """
    Posicionamento profissional com margens invisíveis.
    
    Retorna:
        (x1, y1, x2, y2) — zona do texto (DENTRO da safe zone)
        metodo_override — None (usa paleta normal) ou "sombra" (forçar sombra em foto escura)
    
    NUNCA retorna barra. NUNCA retorna overlay. Texto sempre flutua.
    """
    
    # 1. Safe zone (margens invisíveis)
    safe_zone = get_safe_zone(w, h, formato)
    
    # 2. Máscara proibida (produto + pele) (Auto-resize para segurança)
    target_w, target_h = image.size
    h_mask, w_mask = mask_produto.shape
    if (w_mask, h_mask) != (target_w, target_h):
        m_img = Image.fromarray(mask_produto * 255)
        m_img = m_img.resize((target_w, target_h), Image.NEAREST)
        mask_produto = (np.array(m_img) > 128).astype(np.uint8)

    mask_proibida = criar_mask_proibida(image, mask_produto)
    
    # 3. Candidatos (dentro da safe zone)
    candidatos = gerar_candidatos(w, h, safe_zone, formato_offset)
    
    # 4. Pontuar
    melhor = None
    melhor_score = -9999
    melhor_nome = "fallback"
    
    for c in candidatos:
        score = pontuar_candidato(
            c['rect'], mask_proibida, c['bonus'], w, h
        )
        if score > melhor_score:
            melhor_score = score
            melhor = c['rect']
            melhor_nome = c['nome']
    
    # THRESHOLD MAIS ALTO: 40 (era 15)
    metodo_override = None
    if melhor_score < 40 or melhor is None:
        sx1, sy1, sx2, sy2 = safe_zone
        altura = int((sy2 - sy1) * 0.22)
        melhor = (sx1, sy2 - altura, sx2, sy2)
        melhor_nome = "safe_bottom_forcado"
        metodo_override = "sombra"
    
    # 6. Determinar se precisa forçar sombra
    #    (quando texto vai sobre área escura ou com muito detalhe)
    # Se já foi definido (pelo fallback), mantém. Se não, verifica ocupação.
    x1, y1, x2, y2 = melhor
    
    # Ensure correct integer slicing
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    
    crop_zona = mask_proibida[max(0,y1):min(h,y2), max(0,x1):min(w,x2)]
    
    if crop_zona.size > 0:
        pct_ocupado = np.sum(crop_zona) / crop_zona.size
    else:
        pct_ocupado = 0
    
    if pct_ocupado > 0.30:
        # Zona tem bastante conteúdo → forçar sombra forte pra legibilidade
        metodo_override = "sombra"
    
    print(f"   📐 Posição V3: {melhor_nome} | Score: {melhor_score:.0f} | Ocup: {pct_ocupado:.0%}")
    
    return (x1, y1, x2, y2), metodo_override


# ============================================================
# DEBUG (Visualização das guias — como no Photoshop)
# ============================================================

def debug_guias(image, formato, zona_escolhida, mask_proibida=None,
                output_path="debug_guias.jpg"):
    """
    Gera imagem tipo Photoshop com:
    - Linhas ciano: safe zone (margens)
    - Linhas amarelas: terços
    - Linha verde: golden ratio
    - Retângulo verde: zona escolhida
    - Vermelho semi-transparente: zonas proibidas
    """
    from PIL import ImageDraw
    
    img = image.copy().convert('RGBA')
    w, h = img.size
    draw = ImageDraw.Draw(img)
    
    # Safe zone (ciano — como guias do Photoshop)
    sz = get_safe_zone(w, h, formato)
    for coords in [
        [(sz[0], 0), (sz[0], h)],     # Esquerda
        [(sz[2], 0), (sz[2], h)],     # Direita
        [(0, sz[1]), (w, sz[1])],     # Topo
        [(0, sz[3]), (w, sz[3])],     # Base
    ]:
        draw.line(coords, fill=(0, 255, 255, 150), width=1)
    
    # Terços (amarelo)
    for frac in [0.333, 0.666]:
        draw.line([(0, int(h*frac)), (w, int(h*frac))], fill=(255, 255, 0, 100), width=1)
        draw.line([(int(w*frac), 0), (int(w*frac), h)], fill=(255, 255, 0, 100), width=1)
    
    # Golden ratio (verde)
    draw.line([(0, int(h*0.618)), (w, int(h*0.618))], fill=(0, 255, 0, 100), width=1)
    
    # Zona escolhida (retângulo verde)
    x1, y1, x2, y2 = zona_escolhida
    draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0, 200), width=2)
    
    # Zonas proibidas (vermelho semi-transparente)
    if mask_proibida is not None:
        h_m, w_m = mask_proibida.shape
        if (w_m, h_m) != (w, h):
            from PIL import Image as PILImage
            mask_viz = np.array(
                PILImage.fromarray(mask_proibida * 255).resize((w, h), PILImage.NEAREST)
            ) > 128
        else:
            mask_viz = mask_proibida > 0
        
        overlay = np.zeros((h, w, 4), dtype=np.uint8)
        overlay[mask_viz] = [255, 0, 0, 60]
        img = Image.alpha_composite(img, Image.fromarray(overlay, 'RGBA'))
    
    try:
        img.convert('RGB').save(output_path, quality=90)
        print(f"   🎯 Debug guias: {output_path}")
    except OSError:
        pass
