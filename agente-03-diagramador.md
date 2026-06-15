# 📐 Agente 03 — "O Diagramador"

## Algoritmo de Layout para Posicionamento Inteligente de Texto

---

## 1. Missão

Garantir legibilidade e harmonia visual ao posicionar texto sobre imagens de produto, tomando decisões matemáticas baseadas nos dados fornecidos pelos Agentes 01 e 02.

---

## 2. O Problema que Este Agente Resolve

Mesmo com a máscara de oclusão (Agente 01) e o texto formatado (Agente 02), ainda restam decisões críticas:

- **Onde exatamente** colocar o texto?
- **Qual tamanho** de fonte usar?
- **Qual cor** garante legibilidade sobre aquele fundo específico?
- **Como alinhar** nome do produto e preço de forma harmoniosa?

O Diagramador resolve tudo isso com geometria computacional e regras de design.

---

## 3. Competência Técnica

| Conceito | Descrição |
|---|---|
| **Maximum Inscribed Rectangle** | Encontra o maior retângulo que cabe dentro de uma região irregular |
| **Luminância Relativa** | Calcula o brilho percebido de uma região para decidir cor de texto |
| **Contraste WCAG** | Padrão de acessibilidade para garantir legibilidade mínima |
| **Hierarquia Tipográfica** | Regras de proporção entre título e preço |
| **Grid System** | Sistema de alinhamento baseado em zonas predefinidas |

---

## 4. Stack Tecnológico

| Componente | Tecnologia | Justificativa |
|---|---|---|
| **Cálculo de retângulo** | Algoritmo MIR customizado | Sem dependências externas |
| **Manipulação de imagem** | Pillow (PIL) | Leve e suficiente |
| **Cálculo de luminância** | NumPy | Operações matriciais rápidas |
| **Renderização de texto** | Pillow ImageDraw + ImageFont | Controle total sobre posição |
| **Fontes** | Google Fonts (Montserrat, Inter, Playfair Display) | Gratuitas, alta qualidade |

---

## 5. Pipeline de Processamento

```
┌──────────────────┐     ┌──────────────────┐
│   Agente 01      │     │   Agente 02      │
│  Máscara de      │     │  Texto           │
│  Oclusão +       │     │  Estruturado +   │
│  Zonas Livres    │     │  Métricas de     │
│                  │     │  Tamanho         │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         └───────────┬────────────┘
                     │
              ┌──────▼──────┐
              │  ETAPA 1    │
              │  Encontrar  │
              │  Retângulo  │
              │  Máximo     │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │  ETAPA 2    │
              │  Calcular   │
              │  Luminância │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │  ETAPA 3    │
              │  Definir    │
              │  Tipografia │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │  ETAPA 4    │
              │  Renderizar │
              │  + Validar  │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │  OUTPUT:    │
              │  Imagem     │
              │  Final      │
              └─────────────┘
```

---

## 6. Etapa 1: Maximum Inscribed Rectangle (MIR)

### O que é?

Dado um espaço irregular (a área livre da imagem após remover a zona do produto), o MIR encontra o **maior retângulo** que cabe nesse espaço.

### Implementação

```python
import numpy as np

def maximum_inscribed_rectangle(mask):
    """
    Encontra o maior retângulo inscrito em uma região de 0s (área livre).
    
    mask: numpy array binário (1 = ocupado/proibido, 0 = livre)
    returns: (x, y, width, height) do maior retângulo
    """
    rows, cols = mask.shape
    
    # Passo 1: Calcular alturas (histogram approach)
    heights = np.zeros((rows, cols), dtype=int)
    for i in range(rows):
        for j in range(cols):
            if mask[i][j] == 0:  # Pixel livre
                heights[i][j] = heights[i-1][j] + 1 if i > 0 else 1
            else:
                heights[i][j] = 0
    
    # Passo 2: Para cada linha, encontrar o maior retângulo no histograma
    max_area = 0
    best_rect = (0, 0, 0, 0)
    
    for i in range(rows):
        rect = largest_rectangle_in_histogram(heights[i], i)
        if rect[2] * rect[3] > max_area:
            max_area = rect[2] * rect[3]
            best_rect = rect
    
    return best_rect


def largest_rectangle_in_histogram(heights, current_row):
    """
    Algoritmo de stack para maior retângulo em histograma.
    Complexidade: O(n)
    """
    stack = []
    max_area = 0
    best = (0, 0, 0, 0)  # x, y, w, h
    
    extended = np.append(heights, 0)
    
    for j in range(len(extended)):
        start = j
        while stack and stack[-1][1] > extended[j]:
            idx, h = stack.pop()
            width = j - idx
            area = h * width
            if area > max_area:
                max_area = area
                best = (idx, current_row - h + 1, width, h)
            start = idx
        stack.append((start, extended[j]))
    
    return best
```

### Otimização: Preferência por Zonas de Design

O MIR puro encontra o maior espaço, mas nem sempre o mais bonito. Adicionamos **pesos por zona**:

```python
# Zonas preferidas para posicionamento de texto (pesos multiplicadores)
ZONE_WEIGHTS = {
    "bottom_center": 1.5,    # Melhor posição para preço
    "top_center": 1.3,       # Boa para nome do produto
    "bottom_left": 1.2,      # Alternativa elegante
    "bottom_right": 1.2,     # Alternativa elegante
    "center": 0.5,           # Evitar — compete com produto
    "top_left": 0.8,         # Aceitável
    "top_right": 0.8,        # Aceitável
}

def weighted_mir(mask, image_width, image_height):
    """
    MIR com preferência por zonas de design.
    """
    # Encontra todos os retângulos candidatos (top N)
    candidates = find_top_n_rectangles(mask, n=10)
    
    best_score = 0
    best_rect = None
    
    for rect in candidates:
        x, y, w, h = rect
        area = w * h
        
        # Determinar zona do retângulo
        center_x = (x + w/2) / image_width
        center_y = (y + h/2) / image_height
        zone = classify_zone(center_x, center_y)
        
        weight = ZONE_WEIGHTS.get(zone, 1.0)
        score = area * weight
        
        if score > best_score:
            best_score = score
            best_rect = rect
    
    return best_rect


def classify_zone(rel_x, rel_y):
    """
    Classifica posição relativa em zona nomeada.
    """
    if rel_y > 0.66:
        vertical = "bottom"
    elif rel_y < 0.33:
        vertical = "top"
    else:
        vertical = "center"
    
    if rel_x < 0.33:
        horizontal = "left"
    elif rel_x > 0.66:
        horizontal = "right"
    else:
        horizontal = "center"
    
    if vertical == "center" and horizontal == "center":
        return "center"
    
    return f"{vertical}_{horizontal}"
```

---

## 7. Etapa 2: Cálculo de Luminância

### Por que importa?

Texto preto sobre fundo escuro é invisível. Texto branco sobre fundo claro, idem. Precisamos medir o brilho exato do fundo onde o texto será posicionado.

### Implementação

```python
def calcular_luminancia(imagem, rect):
    """
    Calcula a luminância relativa da região do retângulo.
    
    Fórmula ITU-R BT.709:
    L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    
    Returns: float entre 0.0 (preto) e 1.0 (branco)
    """
    x, y, w, h = rect
    
    # Extrair região
    regiao = np.array(imagem.crop((x, y, x + w, y + h)))
    
    # Normalizar para 0-1
    regiao_norm = regiao / 255.0
    
    # Calcular luminância por pixel
    luminancia = (
        0.2126 * regiao_norm[:, :, 0] +   # Red
        0.7152 * regiao_norm[:, :, 1] +   # Green
        0.0722 * regiao_norm[:, :, 2]     # Blue
    )
    
    return float(np.mean(luminancia))


def decidir_cor_texto(luminancia):
    """
    Decide a cor do texto baseado na luminância do fundo.
    
    Também lida com a "zona cinza" onde nem preto nem branco
    são ideais sozinhos.
    """
    if luminancia > 0.65:
        # Fundo claro → Texto escuro
        return {
            "cor_principal": "#1A1A1A",    # Preto suave
            "cor_sombra": None,
            "usar_sombra": False,
            "usar_outline": False
        }
    elif luminancia < 0.35:
        # Fundo escuro → Texto claro
        return {
            "cor_principal": "#FFFFFF",
            "cor_sombra": None,
            "usar_sombra": False,
            "usar_outline": False
        }
    else:
        # ZONA AMBÍGUA (0.35 a 0.65)
        # Usar texto branco COM sombra para garantir legibilidade
        return {
            "cor_principal": "#FFFFFF",
            "cor_sombra": "#000000",
            "usar_sombra": True,
            "sombra_offset": (2, 2),
            "sombra_blur": 4,
            "usar_outline": True,
            "outline_width": 1,
            "outline_color": "#00000066"  # Preto 40% opacidade
        }
```

### Contraste WCAG

Validação adicional de acessibilidade:

```python
def calcular_contraste_wcag(cor_texto_hex, luminancia_fundo):
    """
    Calcula ratio de contraste WCAG 2.0.
    
    Mínimo para texto normal: 4.5:1
    Mínimo para texto grande (>18pt): 3:1
    """
    # Converter hex para luminância
    r, g, b = hex_to_rgb(cor_texto_hex)
    lum_texto = 0.2126 * (r/255) + 0.7152 * (g/255) + 0.0722 * (b/255)
    
    # Ratio de contraste
    lighter = max(lum_texto, luminancia_fundo)
    darker = min(lum_texto, luminancia_fundo)
    
    ratio = (lighter + 0.05) / (darker + 0.05)
    
    return {
        "ratio": round(ratio, 2),
        "passa_normal": ratio >= 4.5,    # Texto normal (< 18pt)
        "passa_grande": ratio >= 3.0,    # Texto grande (≥ 18pt)
        "nivel": "AAA" if ratio >= 7 else "AA" if ratio >= 4.5 else "FALHA"
    }
```

---

## 8. Etapa 3: Hierarquia Tipográfica

### Sistema de Fontes

```python
TIPOGRAFIA = {
    "paleta_elegante": {
        "produto": {
            "familia": "Playfair Display",
            "peso": "Regular",
            "tracking": 2,  # Espaçamento entre letras (px)
        },
        "preco": {
            "familia": "Montserrat",
            "peso": "Bold",
            "tracking": 0,
        }
    },
    "paleta_moderna": {
        "produto": {
            "familia": "Inter",
            "peso": "Light",
            "tracking": 3,
        },
        "preco": {
            "familia": "Inter",
            "peso": "Bold",
            "tracking": 0,
        }
    },
    "paleta_luxo": {
        "produto": {
            "familia": "Cormorant Garamond",
            "peso": "Regular",
            "tracking": 4,
        },
        "preco": {
            "familia": "Montserrat",
            "peso": "SemiBold",
            "tracking": 1,
        }
    }
}
```

### Cálculo de Tamanho de Fonte

```python
def calcular_tamanho_fonte(rect, texto_produto, texto_preco, formato="feed"):
    """
    Calcula o tamanho ideal de fonte para caber no retângulo disponível.
    
    Regras:
    - Preço: 1.3x maior que nome do produto
    - Margem interna do retângulo: 10%
    - Tamanho mínimo: 14px (legibilidade mobile)
    - Tamanho máximo: varia por formato
    """
    x, y, w, h = rect
    
    # Margem interna
    margem = 0.10
    w_util = w * (1 - 2 * margem)
    h_util = h * (1 - 2 * margem)
    
    # Limites por formato
    LIMITES = {
        "stories":      {"min": 16, "max": 72},
        "feed":         {"min": 14, "max": 56},
        "feed_quadrado": {"min": 14, "max": 48},
    }
    limites = LIMITES.get(formato, LIMITES["feed"])
    
    # Proporção: 2 linhas (produto + preço)
    # Produto ocupa ~40% da altura, preço ~50%, gap ~10%
    h_produto = h_util * 0.38
    h_preco = h_util * 0.50
    
    # Fonte do produto: limitada pela largura E altura
    tam_por_altura_produto = h_produto
    tam_por_largura_produto = (w_util / len(texto_produto)) * 1.8  # Aproximação
    tam_produto = min(tam_por_altura_produto, tam_por_largura_produto)
    
    # Fonte do preço: maior que produto
    tam_preco = tam_produto * 1.3
    
    # Aplicar limites
    tam_produto = max(limites["min"], min(limites["max"], tam_produto))
    tam_preco = max(limites["min"], min(limites["max"] * 1.2, tam_preco))
    
    return {
        "produto_size": int(tam_produto),
        "preco_size": int(tam_preco),
        "margem_x": int(w * margem),
        "margem_y": int(h * margem),
    }
```

---

## 9. Etapa 4: Renderização e Validação

### Renderização Completa

```python
from PIL import Image, ImageDraw, ImageFont

def renderizar_texto(imagem_path, rect, dados_texto, config_cor, config_fonte, paleta="paleta_elegante"):
    """
    Renderiza o texto final sobre a imagem.
    """
    img = Image.open(imagem_path).convert("RGBA")
    
    # Layer de texto (para permitir sombras e transparência)
    txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)
    
    x, y, w, h = rect
    tipografia = TIPOGRAFIA[paleta]
    
    # Carregar fontes
    font_produto = ImageFont.truetype(
        f"fonts/{tipografia['produto']['familia']}-{tipografia['produto']['peso']}.ttf",
        config_fonte["produto_size"]
    )
    font_preco = ImageFont.truetype(
        f"fonts/{tipografia['preco']['familia']}-{tipografia['preco']['peso']}.ttf",
        config_fonte["preco_size"]
    )
    
    # Posições
    pos_x = x + config_fonte["margem_x"]
    pos_produto_y = y + config_fonte["margem_y"]
    pos_preco_y = pos_produto_y + config_fonte["produto_size"] + int(h * 0.08)
    
    cor = config_cor["cor_principal"]
    
    # Sombra (se zona ambígua)
    if config_cor.get("usar_sombra"):
        offset = config_cor["sombra_offset"]
        draw.text(
            (pos_x + offset[0], pos_produto_y + offset[1]),
            dados_texto["produto"],
            font=font_produto,
            fill=config_cor["cor_sombra"]
        )
        draw.text(
            (pos_x + offset[0], pos_preco_y + offset[1]),
            dados_texto["preco"],
            font=font_preco,
            fill=config_cor["cor_sombra"]
        )
    
    # Outline (se zona ambígua)
    if config_cor.get("usar_outline"):
        ow = config_cor["outline_width"]
        oc = config_cor["outline_color"]
        for dx in range(-ow, ow + 1):
            for dy in range(-ow, ow + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((pos_x + dx, pos_produto_y + dy),
                         dados_texto["produto"], font=font_produto, fill=oc)
                draw.text((pos_x + dx, pos_preco_y + dy),
                         dados_texto["preco"], font=font_preco, fill=oc)
    
    # Texto principal
    draw.text((pos_x, pos_produto_y), dados_texto["produto"],
              font=font_produto, fill=cor)
    draw.text((pos_x, pos_preco_y), dados_texto["preco"],
              font=font_preco, fill=cor)
    
    # Compor layers
    resultado = Image.alpha_composite(img, txt_layer)
    
    return resultado.convert("RGB")
```

### Validação Final

```python
def validar_resultado(imagem_original, imagem_final, mask_produto, rect_texto):
    """
    Validação automática do resultado final.
    Retorna score de qualidade e alertas.
    """
    validacoes = []
    score = 100
    
    # Validação 1: Texto não sobrepõe produto
    x, y, w, h = rect_texto
    regiao_texto = mask_produto[y:y+h, x:x+w]
    pixels_sobrepostos = np.sum(regiao_texto == 1)
    
    if pixels_sobrepostos > 0:
        score -= 50
        validacoes.append({
            "tipo": "ERRO_CRITICO",
            "msg": f"Texto sobrepõe {pixels_sobrepostos} pixels do produto"
        })
    
    # Validação 2: Contraste WCAG
    luminancia = calcular_luminancia(Image.open(imagem_original), rect_texto)
    contraste = calcular_contraste_wcag("#FFFFFF", luminancia)
    
    if not contraste["passa_grande"]:
        score -= 30
        validacoes.append({
            "tipo": "ALERTA",
            "msg": f"Contraste insuficiente: {contraste['ratio']}:1 (mínimo 3:1)"
        })
    
    # Validação 3: Texto dentro dos limites da imagem
    img_w, img_h = Image.open(imagem_original).size
    if x + w > img_w or y + h > img_h:
        score -= 40
        validacoes.append({
            "tipo": "ERRO",
            "msg": "Texto ultrapassa limites da imagem"
        })
    
    # Validação 4: Tamanho mínimo legível
    # (assume que a imagem será vista em tela mobile ~375px de largura)
    escala_mobile = 375 / img_w
    # Se o menor texto renderizado for < 10px em mobile, é ilegível
    
    return {
        "score": max(0, score),
        "aprovado": score >= 70,
        "validacoes": validacoes
    }
```

---

## 10. Templates por Formato

```python
TEMPLATES = {
    "instagram_feed_quadrado": {
        "dimensoes": (1080, 1080),
        "zonas_texto_preferidas": [
            {"nome": "bottom_bar", "rect": (0, 810, 1080, 270), "peso": 1.5},
            {"nome": "top_bar", "rect": (0, 0, 1080, 200), "peso": 1.2},
        ],
        "margem_segura": 40,  # px do edge (safe area)
    },
    "instagram_feed_retrato": {
        "dimensoes": (1080, 1350),
        "zonas_texto_preferidas": [
            {"nome": "bottom_bar", "rect": (0, 1050, 1080, 300), "peso": 1.5},
            {"nome": "top_bar", "rect": (0, 0, 1080, 220), "peso": 1.2},
        ],
        "margem_segura": 40,
    },
    "instagram_stories": {
        "dimensoes": (1080, 1920),
        "zonas_texto_preferidas": [
            {"nome": "bottom_third", "rect": (0, 1280, 1080, 500), "peso": 1.5},
            {"nome": "top_area", "rect": (0, 120, 1080, 300), "peso": 1.0},
            # Evitar topo (câmera/hora) e rodapé (swipe up)
        ],
        "margem_segura": 60,
        "zona_proibida_topo": 100,     # Status bar
        "zona_proibida_rodape": 140,   # Swipe up / botões
    },
    "whatsapp_status": {
        "dimensoes": (1080, 1920),
        "zonas_texto_preferidas": [
            {"nome": "center_bottom", "rect": (100, 1200, 880, 500), "peso": 1.4},
        ],
        "margem_segura": 80,
    }
}
```

---

## 11. Paletas de Marca

```python
PALETAS_MARCA = {
    "classica": {
        "cor_primaria": "#1A1A1A",
        "cor_secundaria": "#C9A96E",     # Dourado
        "cor_fundo_fallback": "#F5F0EB",  # Bege claro
        "fonte_titulo": "Playfair Display",
        "fonte_corpo": "Montserrat",
    },
    "moderna": {
        "cor_primaria": "#2D2D2D",
        "cor_secundaria": "#E8B4B8",      # Rosé
        "cor_fundo_fallback": "#FAFAFA",
        "fonte_titulo": "Inter",
        "fonte_corpo": "Inter",
    },
    "luxo": {
        "cor_primaria": "#0D0D0D",
        "cor_secundaria": "#D4AF37",      # Ouro
        "cor_fundo_fallback": "#1A1A1A",
        "fonte_titulo": "Cormorant Garamond",
        "fonte_corpo": "Montserrat",
    }
}
```

---

## 12. Fluxo Completo de Decisão

```
                    ┌─────────────────────┐
                    │  Receber dados dos   │
                    │  Agentes 01 e 02     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Detectar formato    │
                    │  da imagem           │
                    │  (1:1, 4:5, 9:16)   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Selecionar template │
                    │  + zonas preferidas  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Executar Weighted   │
                    │  MIR nas zonas       │
                    │  livres              │
                    └──────────┬──────────┘
                               │
              ┌────────────────▼────────────────┐
              │  Retângulo encontrado é grande   │
              │  o suficiente para o texto?      │
              └──┬───────────────────────────┬───┘
              SIM│                           │NÃO
                 ▼                           ▼
          ┌────────────┐          ┌──────────────────┐
          │  Calcular  │          │  Reduzir fonte   │
          │  luminância│          │  até caber OU    │
          │  + cor     │          │  tentar zona     │
          └─────┬──────┘          │  secundária      │
                │                 └────────┬─────────┘
                ▼                          │
          ┌────────────┐                   │
          │  Calcular  │◀──────────────────┘
          │  tipografia│
          └─────┬──────┘
                │
          ┌─────▼──────┐
          │  Renderizar│
          └─────┬──────┘
                │
          ┌─────▼──────┐
          │  Validar   │
          │  WCAG +    │──── FALHA ──▶ Tentar cor/posição alternativa
          │  Oclusão   │
          └─────┬──────┘
                │ OK
          ┌─────▼──────┐
          │  IMAGEM    │
          │  FINAL     │
          └────────────┘
```

---

## 13. Output Final

```json
{
  "imagem_final_path": "/output/colar_pedra_verde_final.jpg",
  "layout_aplicado": {
    "formato_detectado": "instagram_feed_quadrado",
    "template_usado": "instagram_feed_quadrado",
    "paleta_usada": "classica",
    "retangulo_texto": {
      "x": 40, "y": 820, "w": 1000, "h": 220
    },
    "zona_selecionada": "bottom_bar",
    "luminancia_fundo": 0.82,
    "cor_texto_aplicada": "#1A1A1A",
    "fonte_produto": {
      "familia": "Playfair Display",
      "tamanho": 28,
      "peso": "Regular"
    },
    "fonte_preco": {
      "familia": "Montserrat",
      "tamanho": 36,
      "peso": "Bold"
    }
  },
  "validacao": {
    "score": 95,
    "aprovado": true,
    "contraste_wcag": {
      "ratio": 8.2,
      "nivel": "AAA"
    },
    "oclusao_produto": false,
    "texto_dentro_limites": true
  },
  "tempo_processamento_ms": 180
}
```

---

## 14. Métricas de Qualidade

| Métrica | Meta | Como Medir |
|---|---|---|
| **Score de Validação** | > 85/100 | Pipeline automático de validação |
| **Contraste WCAG** | ≥ AA (4.5:1) | Cálculo automático por imagem |
| **Zero Oclusão** | 100% | Verificação pixel-a-pixel |
| **Tempo de Layout** | < 200ms | Benchmark do algoritmo MIR + renderização |
| **Satisfação Visual** | > 4/5 | Avaliação humana periódica (amostragem) |

---

## 15. Tratamento de Casos Extremos

| Cenário | Solução |
|---|---|
| Produto ocupa >85% da imagem | Adicionar barra semitransparente no rodapé para texto |
| Fundo muito texturizado | Usar backdrop blur ou faixa com opacidade |
| Texto do produto muito longo | Quebrar em 2 linhas; se ainda não couber, abreviar com "..." |
| Múltiplos produtos na foto | Posicionar texto em área neutra, sem associar a produto específico |
| Imagem vertical em template quadrado | Crop inteligente ou letterbox com cor da paleta |

### Barra Semitransparente (Fallback)

```python
def adicionar_barra_texto(imagem, posicao="bottom", altura_pct=0.25, opacidade=0.7):
    """
    Quando não há espaço livre suficiente, adiciona uma barra
    semitransparente para garantir legibilidade.
    """
    img = imagem.convert("RGBA")
    w, h = img.size
    
    altura_barra = int(h * altura_pct)
    
    overlay = Image.new("RGBA", (w, altura_barra), (0, 0, 0, int(255 * opacidade)))
    
    if posicao == "bottom":
        pos_y = h - altura_barra
    else:
        pos_y = 0
    
    img.paste(overlay, (0, pos_y), overlay)
    
    return img, (0, pos_y, w, altura_barra)
```

---

> **Resumo:** O Diagramador é o cérebro matemático que une os dados dos outros dois agentes e toma a decisão final de onde, como e com qual aparência o texto será renderizado — garantindo que toda imagem saia profissional, legível e com a joia em destaque.
