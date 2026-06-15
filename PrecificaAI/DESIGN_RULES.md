# 📐 Regras de Diagramação Profissional - PrecificaAI

## 🎯 Objetivo
Posicionar texto de forma **profissional e harmônica** usando princípios de design gráfico comprovados.

---

## 📏 1. ZONAS SEGURAS (Safe Zones)

### Para Instagram/Redes Sociais:
```
┌─────────────────────────┐
│ ▓▓▓ ZONA MORTA ▓▓▓      │ ← 10-15% superior (cortado em feeds)
├─────────────────────────┤
│                         │
│   ZONA SEGURA           │ ← 70-80% central (sempre visível)
│   (Texto aqui)          │
│                         │
├─────────────────────────┤
│ ▓▓▓ ZONA MORTA ▓▓▓      │ ← 10-15% inferior (cortado em feeds)
└─────────────────────────┘
```

**Implementação:**
- **Feed Quadrado (1080x1080):** Zona segura = 1080x864px (centro)
- **Stories (1080x1920):** Zona segura = 1080x1536px (centro)
- **Reels (1080x1920):** Zona segura = 1080x1536px (centro)

---

## 🌀 2. GOLDEN RATIO (Proporção Áurea - φ ≈ 1.618)

### Divisão Fibonacci:
```
┌──────────────────────────┐
│          38.2%           │ ← Zona superior (título/logo)
├──────────────────────────┤
│                          │
│         61.8%            │ ← Zona inferior (preço/CTA)
│      (Golden Zone)       │
│                          │
└──────────────────────────┘
```

**Pontos de Interesse (Power Points):**
- **Superior:** 38.2% da altura
- **Inferior:** 61.8% da altura (GOLDEN SPOT - melhor para preço!)

---

## 📐 3. RULE OF THIRDS (Regra dos Terços)

### Grid 3x3:
```
┌─────┬─────┬─────┐
│  1  │  2  │  3  │
├─────┼─────┼─────┤
│  4  │  5  │  6  │ ← Linha central (eixo visual)
├─────┼─────┼─────┤
│  7  │  8  │  9  │
└─────┴─────┴─────┘

Pontos Fortes: 2, 4, 5, 6, 8
Melhor para texto: 5 (centro) ou 8 (inferior central)
```

**Intersecções (Hot Spots):**
- Horizontal: 33.3%, 66.6%
- Vertical: 33.3%, 66.6%

---

## 🎨 4. HIERARQUIA VISUAL

### Ordem de Leitura (padrão F ou Z):
```
1. TÍTULO (topo/esquerda)
   ↓
2. PREÇO (centro/destaque)
   ↓
3. PARCELAS (abaixo do preço)
```

### Tamanhos Relativos:
- **Título:** 100% (base)
- **Preço:** 130-150% do título (DESTAQUE)
- **Parcelas:** 70-80% do título (secundário)

---

## 🚫 5. ZONAS PROIBIDAS (Evitar)

### Onde NÃO colocar texto:
1. **Cantos extremos** (< 5% das bordas)
2. **Sobre o produto** (detectado pela máscara)
3. **Zonas de corte** (topo/base em feeds)
4. **Áreas de baixo contraste** (fundo similar à cor do texto)

---

## ✅ 6. SISTEMA DE PONTUAÇÃO (Scoring)

### Algoritmo de Escolha da Melhor Posição:

```python
def calcular_score(zona, mask, contraste, formato):
    score = 100
    
    # 1. Penalizar sobreposição com produto
    sobreposicao = calcular_sobreposicao(zona, mask)
    score -= sobreposicao * 50  # -50 pontos se 100% sobreposto
    
    # 2. Bonificar Golden Ratio
    if esta_na_golden_zone(zona):
        score += 30
    
    # 3. Bonificar Rule of Thirds
    if esta_em_power_point(zona):
        score += 20
    
    # 4. Bonificar contraste
    score += contraste * 20  # 0-20 pontos
    
    # 5. Penalizar zonas mortas (Instagram)
    if formato == "feed" and esta_em_zona_morta(zona):
        score -= 40
    
    return score
```

---

## 📱 7. REGRAS POR FORMATO

### A. Feed Quadrado (1080x1080)
```
Zona Morta Superior: 0-135px
Zona Segura: 135-945px (810px úteis)
Zona Morta Inferior: 945-1080px

Posição Ideal: 61.8% = ~660px (Golden Ratio)
```

### B. Stories/Reels (1080x1920)
```
Zona Morta Superior: 0-250px
Zona Segura: 250-1670px (1420px úteis)
Zona Morta Inferior: 1670-1920px

Posição Ideal: 61.8% = ~1186px (Golden Ratio)
```

### C. Original (Variável)
```
Sem zonas mortas
Usar Golden Ratio ou Rule of Thirds
Priorizar contraste e evitar produto
```

---

## 🎯 8. IMPLEMENTAÇÃO NO DIAGRAMADOR

### Fluxo de Decisão:
```
1. Detectar formato (original/feed/stories)
2. Calcular zonas seguras
3. Aplicar máscara do produto (Topógrafo)
4. Gerar candidatos:
   - Golden Ratio (superior + inferior)
   - Rule of Thirds (4 pontos)
   - Centro (fallback)
5. Calcular score de cada candidato
6. Escolher o melhor (maior score)
7. Ajustar margens finais (5% laterais, 3% topo, 5% base)
```

---

## 📊 9. EXEMPLOS PRÁTICOS

### Caso 1: Anel no centro da foto
```
Produto: Centro (máscara alta)
Solução: Texto na zona inferior (61.8%)
Razão: Golden Ratio + Zona Segura
```

### Caso 2: Colar vertical
```
Produto: Vertical central
Solução: Texto lateral (esquerda ou direita)
Razão: Rule of Thirds (33.3% ou 66.6%)
```

### Caso 3: Brincos pequenos no topo
```
Produto: Topo
Solução: Texto na zona inferior central
Razão: Contraste + Golden Ratio
```

---

## 🔧 10. PARÂMETROS AJUSTÁVEIS

```python
SAFE_ZONES = {
    "feed_quadrado": {
        "top_dead": 0.125,      # 12.5% topo
        "bottom_dead": 0.125,   # 12.5% base
    },
    "stories": {
        "top_dead": 0.13,       # 13% topo
        "bottom_dead": 0.13,    # 13% base
    },
    "original": {
        "top_dead": 0.0,
        "bottom_dead": 0.0,
    }
}

GOLDEN_RATIO = 0.618
RULE_OF_THIRDS = [0.333, 0.667]

MARGINS = {
    "lateral": 0.05,   # 5% cada lado
    "top": 0.03,       # 3% topo
    "bottom": 0.05,    # 5% base
}

WEIGHTS = {
    "overlap_penalty": -50,
    "golden_bonus": 30,
    "thirds_bonus": 20,
    "contrast_bonus": 20,
    "dead_zone_penalty": -40,
}
```

---

## 🎓 REFERÊNCIAS

1. **Golden Ratio:** Da Vinci, Fibonacci
2. **Rule of Thirds:** Fotografia profissional
3. **Safe Zones:** Instagram Guidelines 2024
4. **Hierarquia Visual:** Gestalt Principles

---

## 🚀 PRÓXIMOS PASSOS

1. ✅ Implementar `calcular_golden_zones()`
2. ✅ Implementar `calcular_thirds_grid()`
3. ✅ Implementar `scoring_system()`
4. ✅ Integrar no `encontrar_melhor_posicao()`
5. ⏳ Adicionar modo "debug" com grid visual
6. ⏳ A/B testing com usuários reais
