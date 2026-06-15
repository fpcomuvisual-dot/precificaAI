"""
Ponte: Agente 01 (Topógrafo) → renderCanvas.js

Problema:
    O Topógrafo entrega `free_zones` com coordenadas no espaço da imagem
    processada (1024×1024 com letterboxing/padding).

    O renderCanvas.js espera `boxes` como arrays [x, y, w, h] no espaço
    da imagem ORIGINAL (antes do letterbox).

Esta ponte faz a conversão em duas direções:
    1. Lado Python (backend): converte free_zones → boxes antes de responder a API
    2. Lado JS (frontend, embutido abaixo): versão idêntica para uso no browser

Também expõe `selecionar_melhor_zona()` que escolhe a zona mais adequada
para modo single-card (1 produto), e `zonas_para_pinos()` para modo multi-preço.
"""

from typing import Optional
import json


# ---------------------------------------------------------------------------
# Constantes de Preferência de Zona (espelha o Agente 03)
# ---------------------------------------------------------------------------

PESOS_ZONA = {
    "bottom_center": 1.5,
    "top_center":    1.3,
    "bottom_left":   1.2,
    "bottom_right":  1.2,
    "top_left":      0.8,
    "top_right":     0.8,
    "center":        0.5,  # Evitar — compete com produto
}


def _classificar_zona(rel_x: float, rel_y: float) -> str:
    """Classifica posição relativa (0-1) em zona nomeada."""
    v = "bottom" if rel_y > 0.66 else ("top" if rel_y < 0.33 else "center")
    h = "left"   if rel_x < 0.33 else ("right" if rel_x > 0.66 else "center")
    if v == "center" and h == "center":
        return "center"
    return f"{v}_{h}"


# ---------------------------------------------------------------------------
# Conversão de Coordenadas: espaço letterbox → espaço original
# ---------------------------------------------------------------------------

def reverter_letterbox(
    coords: dict,
    meta: dict,
) -> dict:
    """
    Converte coordenadas do espaço processado (1024×1024 com padding)
    para o espaço da imagem ORIGINAL.

    Args:
        coords: {"x": int, "y": int, "w": int, "h": int}
                — coordenadas dentro da imagem letterboxada (processed_dims)
        meta:   bloco "meta" do JSON do Agente 01
                {
                  "original_dims": [orig_w, orig_h],
                  "processed_dims": [proc_w, proc_h],
                  "padding": {"top": int, "bottom": int, "left": int, "right": int},
                  "scale_factor": float
                }

    Returns:
        {"x": int, "y": int, "w": int, "h": int} no espaço original
    """
    pad   = meta["padding"]
    scale = meta["scale_factor"]   # escala aplicada: original → processado (sem pad)
    orig_w, orig_h = meta["original_dims"]

    # Remover padding
    x_sem_pad = coords["x"] - pad["left"]
    y_sem_pad = coords["y"] - pad["top"]

    # Reverter escala
    x_orig = x_sem_pad / scale
    y_orig = y_sem_pad / scale
    w_orig = coords["w"] / scale
    h_orig = coords["h"] / scale

    # Clamp nos limites da imagem original
    x_orig = max(0.0, x_orig)
    y_orig = max(0.0, y_orig)
    w_orig = min(w_orig, orig_w - x_orig)
    h_orig = min(h_orig, orig_h - y_orig)

    return {
        "x": round(x_orig),
        "y": round(y_orig),
        "w": round(w_orig),
        "h": round(h_orig),
    }


# ---------------------------------------------------------------------------
# Selecionar Melhor Zona (Modo Single Card)
# ---------------------------------------------------------------------------

def selecionar_melhor_zona(topografo_output: dict) -> Optional[dict]:
    """
    Recebe o JSON completo do Agente 01 e retorna a MELHOR zona livre
    para posicionar o bloco de texto único (nome + preço).

    Critério: área_px × peso_de_zona

    Returns:
        {
          "zona_id": str,
          "box_original": [x, y, w, h],   ← formato direto para renderCanvas
          "luminancia": float,
          "cor_sugerida": str,             ← "#FFFFFF" ou "#000000"
          "score": float,
        }
        ou None se failsafe_triggered e não há zonas
    """
    meta  = topografo_output["meta"]
    zonas = topografo_output.get("free_zones", [])

    if not zonas:
        return None  # Caller deve usar fallback de barra opaca

    melhor_score = -1
    melhor = None

    for zona in zonas:
        coords = zona["coords"]   # x, y, w, h no espaço processado
        area   = zona["area_px"]
        props  = zona["properties"]

        # Centro relativo no espaço processado
        proc_w, proc_h = meta["processed_dims"]
        rel_x = (coords["x"] + coords["w"] / 2) / proc_w
        rel_y = (coords["y"] + coords["h"] / 2) / proc_h

        zona_nome = _classificar_zona(rel_x, rel_y)
        peso      = PESOS_ZONA.get(zona_nome, 1.0)
        score     = area * peso

        if score > melhor_score:
            melhor_score = score
            # Converter para espaço original
            box_orig = reverter_letterbox(coords, meta)
            melhor = {
                "zona_id":     zona["id"],
                "zona_nome":   zona_nome,
                "box_original": [
                    box_orig["x"],
                    box_orig["y"],
                    box_orig["w"],
                    box_orig["h"],
                ],
                "luminancia":   props["avg_luminance"] / 255,  # normalizar 0-1
                "cor_sugerida": props["suggested_font_color"],
                "score":        round(score, 1),
            }

    return melhor


# ---------------------------------------------------------------------------
# Converter Todas as Zonas em Boxes (Modo Pinos / Multi-preço)
# ---------------------------------------------------------------------------

def zonas_para_boxes(topografo_output: dict) -> list:
    """
    Converte TODAS as free_zones em boxes no espaço original,
    mantendo a ordem de score decrescente.

    Returns:
        Lista de [x, y, w, h] — formato direto para o array `boxes`
        do renderCanvas.js
    """
    meta  = topografo_output["meta"]
    zonas = topografo_output.get("free_zones", [])

    resultado = []
    for zona in zonas:
        coords   = zona["coords"]
        box_orig = reverter_letterbox(coords, meta)
        resultado.append([
            box_orig["x"],
            box_orig["y"],
            box_orig["w"],
            box_orig["h"],
        ])
    return resultado


# ---------------------------------------------------------------------------
# Montagem do Payload Final para a API (une Agentes 01, 02 e 03)
# ---------------------------------------------------------------------------

def montar_payload_render(
    topografo_output: dict,
    editor_output: dict,
    config: dict,
) -> dict:
    """
    Recebe os outputs dos Agentes 01 e 02 e retorna o payload pronto
    para ser enviado ao frontend (que passa para renderCanvas.js).

    Args:
        topografo_output: JSON completo do Agente 01
        editor_output:    JSON do Agente 02 (produto, preco, etc.)
        config:           Configurações do usuário {formato, paleta, modo_preco}

    Returns:
        {
          "detalhes": str,       → nome do produto
          "preco": str,          → preço formatado
          "formato": str,        → 'orig' | '1:1' | 'story' | '4:5'
          "mostrarPreco": bool,
          "mostrarParcelas": bool,
          "boxes": list,         → coordenadas no espaço original
          "zona_selecionada": dict,
          "cor_texto": str,
        }
    """
    modo_preco = config.get("modo_preco", "padrao")

    # Mapeamento de formato (frontend → renderCanvas)
    FORMATO_MAP = {
        "original":      "orig",
        "feed_quadrado": "1:1",
        "stories":       "story",
        "feed_retrato":  "4:5",
        "orig":          "orig",   # já no formato correto
        "1:1":           "1:1",
        "story":         "story",
        "4:5":           "4:5",
    }

    formato_canvas = FORMATO_MAP.get(config.get("formato", "original"), "orig")

    # Determinar boxes (modo pinos vs. single)
    boxes = zonas_para_boxes(topografo_output)
    zona  = selecionar_melhor_zona(topografo_output)

    # Determinar o que exibir
    mostrar_preco     = modo_preco in ("padrao", "ambos", "promocao")
    mostrar_parcelas  = modo_preco in ("parcelado", "ambos")

    preco_str = editor_output.get("preco", "")
    if modo_preco == "parcelado" and editor_output.get("parcelas"):
        preco_str = editor_output["parcelas"]
    elif modo_preco == "ambos":
        parcelas = editor_output.get("parcelas", "")
        preco_str = f"{editor_output.get('preco', '')} ou {parcelas}" if parcelas else preco_str

    payload = {
        "detalhes":        editor_output.get("produto", ""),
        "preco":           preco_str,
        "formato":         formato_canvas,
        "mostrarPreco":    mostrar_preco,
        "mostrarParcelas": mostrar_parcelas,
        "boxes":           boxes,
        "zona_selecionada": zona,
        "cor_texto":       zona["cor_sugerida"] if zona else "#FFFFFF",
    }

    return payload


# ---------------------------------------------------------------------------
# Versão JavaScript da Conversão (para embutir no frontend se necessário)
# ---------------------------------------------------------------------------

JS_BRIDGE = """\
/**
 * Ponte Topógrafo → renderCanvas (versão JS)
 * Cole este bloco no frontend se quiser fazer a conversão client-side.
 */

const PESOS_ZONA = {
  bottom_center: 1.5, top_center: 1.3,
  bottom_left: 1.2,   bottom_right: 1.2,
  top_left: 0.8,      top_right: 0.8,
  center: 0.5,
};

function classificarZona(relX, relY) {
  const v = relY > 0.66 ? 'bottom' : relY < 0.33 ? 'top' : 'center';
  const h = relX < 0.33 ? 'left'  : relX > 0.66  ? 'right' : 'center';
  return (v === 'center' && h === 'center') ? 'center' : `${v}_${h}`;
}

function reverterLetterbox(coords, meta) {
  const { padding: pad, scale_factor: scale, original_dims } = meta;
  const [origW, origH] = original_dims;
  let x = (coords.x - pad.left) / scale;
  let y = (coords.y - pad.top)  / scale;
  let w = coords.w / scale;
  let h = coords.h / scale;
  x = Math.max(0, x);
  y = Math.max(0, y);
  w = Math.min(w, origW - x);
  h = Math.min(h, origH - y);
  return { x: Math.round(x), y: Math.round(y), w: Math.round(w), h: Math.round(h) };
}

export function zonasParaBoxes(topografoOutput) {
  const { meta, free_zones = [] } = topografoOutput;
  return free_zones.map(zona => {
    const b = reverterLetterbox(zona.coords, meta);
    return [b.x, b.y, b.w, b.h];
  });
}

export function selecionarMelhorZona(topografoOutput) {
  const { meta, free_zones = [] } = topografoOutput;
  const [procW, procH] = meta.processed_dims;
  let melhor = null, melhorScore = -1;

  for (const zona of free_zones) {
    const { coords, area_px, properties: props } = zona;
    const relX = (coords.x + coords.w / 2) / procW;
    const relY = (coords.y + coords.h / 2) / procH;
    const zonaNome = classificarZona(relX, relY);
    const peso  = PESOS_ZONA[zonaNome] ?? 1.0;
    const score = area_px * peso;

    if (score > melhorScore) {
      melhorScore = score;
      const b = reverterLetterbox(coords, meta);
      melhor = {
        zonaId: zona.id,
        zonaNome,
        boxOriginal: [b.x, b.y, b.w, b.h],
        luminancia: props.avg_luminance / 255,
        corSugerida: props.suggested_font_color,
        score,
      };
    }
  }
  return melhor;
}
"""


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

def _run_tests():
    # JSON de exemplo do Agente 01 (imagem 1080×1920, letterboxed para 1024×1024)
    topografo_mock = {
        "meta": {
            "original_dims": [1080, 1920],
            "processed_dims": [1024, 1024],
            "padding": {"top": 0, "bottom": 0, "left": 219, "right": 219},
            "scale_factor": 0.5333,
        },
        "free_zones": [
            {
                "id": "zone_bottom_center",
                "coords": {"x": 219, "y": 820, "w": 586, "h": 150},
                "area_px": 87900,
                "properties": {
                    "avg_luminance": 35,
                    "suggested_font_color": "#FFFFFF",
                    "contrast_ratio": 14.1,
                }
            },
            {
                "id": "zone_top_center",
                "coords": {"x": 219, "y": 10, "w": 586, "h": 120},
                "area_px": 70320,
                "properties": {
                    "avg_luminance": 220,
                    "suggested_font_color": "#000000",
                    "contrast_ratio": 11.2,
                }
            },
        ],
        "failsafe_triggered": False,
    }

    editor_mock = {
        "produto": "Brinco Prata Zircônia",
        "preco": "R$ 145,00",
        "preco_valor": 145.0,
        "categoria": "Brinco",
        "parcelas": "5x R$ 29,00",
    }

    config_mock = {"formato": "stories", "paleta": "classico", "modo_preco": "ambos"}

    print("=== Teste: reverter_letterbox ===")
    coords_teste = {"x": 219, "y": 820, "w": 586, "h": 150}
    resultado = reverter_letterbox(coords_teste, topografo_mock["meta"])
    print(f"  Entrada (letterbox): {coords_teste}")
    print(f"  Saída (original):    {resultado}")
    # Esperado aprox: x=0, y=1537, w=1098→clamp a 1080, h=281
    assert resultado["x"] == 0, f"x esperado 0, obtido {resultado['x']}"
    assert resultado["y"] > 1500, f"y esperado ~1537, obtido {resultado['y']}"
    print("  ✅ OK\\n")

    print("=== Teste: selecionar_melhor_zona ===")
    zona = selecionar_melhor_zona(topografo_mock)
    print(f"  Zona selecionada: {zona['zona_nome']} (score {zona['score']})")
    print(f"  Box original: {zona['box_original']}")
    print(f"  Cor sugerida: {zona['cor_sugerida']}")
    assert zona["zona_nome"] == "bottom_center", f"Esperado bottom_center, obtido {zona['zona_nome']}"
    assert zona["cor_sugerida"] == "#FFFFFF"
    print("  ✅ OK\\n")

    print("=== Teste: zonas_para_boxes ===")
    boxes = zonas_para_boxes(topografo_mock)
    print(f"  Total boxes: {len(boxes)}")
    for i, b in enumerate(boxes):
        print(f"  Box {i}: {b}")
    assert len(boxes) == 2
    print("  ✅ OK\\n")

    print("=== Teste: montar_payload_render ===")
    payload = montar_payload_render(topografo_mock, editor_mock, config_mock)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    assert payload["formato"] == "story"           # mapeamento correto
    assert payload["detalhes"] == "Brinco Prata Zircônia"
    assert "ou" in payload["preco"]                # modo ambos
    assert len(payload["boxes"]) == 2
    print("  ✅ OK\\n")

    print("=== Teste: failsafe (sem zonas livres) ===")
    topografo_vazio = {**topografo_mock, "free_zones": [], "failsafe_triggered": True}
    zona_vazia = selecionar_melhor_zona(topografo_vazio)
    boxes_vazias = zonas_para_boxes(topografo_vazio)
    assert zona_vazia is None
    assert boxes_vazias == []
    print("  ✅ OK — caller deve usar barra opaca como fallback\\n")

    print("=" * 50)
    print("Todos os testes passaram ✅")


if __name__ == "__main__":
    _run_tests()
    print("\\n\\n--- JS Bridge (copie para o frontend) ---")
    print(JS_BRIDGE)
