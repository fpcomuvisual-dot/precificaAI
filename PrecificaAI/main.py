"""
Precifica.AI — Backend Principal
FastAPI (produção) / Flask (dev local)

Endpoint principal:
    POST /api/processar/batch

Estrutura de pastas esperada:
    agents/
        agente_02_editor.py
        agente_01_bridge.py
    static/
        output/   ← imagens geradas salvas aqui
    main.py

Para rodar em dev (Flask):
    python main.py

Para rodar em produção (FastAPI + uvicorn):
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"""

import base64
import io
import os
import sys
import time
import uuid
import json
import traceback
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Resolver paths dos agentes (compatível com a pasta agents/ do projeto)
# ---------------------------------------------------------------------------

BASE_DIR    = Path(__file__).parent
AGENTS_DIR  = BASE_DIR / "agents"
OUTPUT_DIR  = BASE_DIR / "static" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Adiciona agents/ ao sys.path para importar os módulos
sys.path.insert(0, str(AGENTS_DIR))

from agente_02_editor import processar_texto       # type: ignore
from agente_01_bridge import (                      # type: ignore
    selecionar_melhor_zona,
    zonas_para_boxes,
    montar_payload_render,
)

# ---------------------------------------------------------------------------
# PIL para composição de imagem
# ---------------------------------------------------------------------------

from PIL import Image, ImageDraw, ImageFont


# ===========================================================================
# AGENTE 01 — TOPÓGRAFO
# Troque _mock_topografo() pela chamada real quando o modelo estiver pronto.
# ===========================================================================

def _mock_topografo(image_pil: Image.Image) -> dict:
    """
    Mock do Agente 01 (Topógrafo).

    Retorna uma zona inferior segura (35% da altura) como área livre padrão.
    Simula failsafe_triggered=True para indicar que é o fallback geométrico.

    ⚠️  SUBSTITUIR por chamada real:
        - Roboflow Inference API  →  POST https://detect.roboflow.com/...
        - DIS local               →  onnxruntime session.run(...)
    """
    orig_w, orig_h = image_pil.size

    # Escala para 1024×1024 com letterbox
    scale = min(1024 / orig_w, 1024 / orig_h)
    nw    = int(orig_w * scale)
    nh    = int(orig_h * scale)
    pad_l = (1024 - nw) // 2
    pad_t = (1024 - nh) // 2

    # Zona livre: faixa inferior de 30% da imagem processada (sem padding)
    zona_h  = int(nh * 0.30)
    zona_y  = pad_t + nh - zona_h
    zona_x  = pad_l
    zona_w  = nw

    # Luminância estimada: escurece o fundo via degradê — assume fundo escuro
    # (valor seguro para texto branco — o Agente 03 irá confirmar)
    avg_lum = 40

    return {
        "meta": {
            "original_dims":  [orig_w, orig_h],
            "processed_dims": [1024, 1024],
            "padding": {
                "top":    pad_t,
                "bottom": 1024 - pad_t - nh,
                "left":   pad_l,
                "right":  1024 - pad_l - nw,
            },
            "scale_factor": round(scale, 6),
        },
        "free_zones": [
            {
                "id":       "zone_bottom_safe",
                "type":     "rectangle",
                "coords":   {"x": zona_x, "y": zona_y, "w": zona_w, "h": zona_h},
                "area_px":  zona_w * zona_h,
                "properties": {
                    "avg_luminance":        avg_lum,
                    "suggested_font_color": "#FFFFFF",
                    "contrast_ratio":       14.0,
                },
            }
        ],
        "failsafe_triggered": True,  # ← mudar para False quando modelo real estiver ativo
    }


def chamar_topografo(image_pil: Image.Image) -> dict:
    """
    Ponto de injeção do Agente 01.
    Hoje chama o mock. Amanhã chama o modelo real.
    """
    # TODO: substituir por chamada real
    # from agente_01_topografo import analisar_imagem
    # return analisar_imagem(image_pil)
    return _mock_topografo(image_pil)


# ===========================================================================
# RENDERIZAÇÃO — Composição final da imagem com Pillow
# ===========================================================================

def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _carregar_fonte(tamanho: int, negrito: bool = False) -> ImageFont.ImageFont:
    """Tenta carregar fonte do sistema; fallback para default do Pillow."""
    candidatos_bold   = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                         "C:/Windows/Fonts/arialbd.ttf",
                         "/System/Library/Fonts/Helvetica.ttc"]
    candidatos_normal = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                         "C:/Windows/Fonts/arial.ttf",
                         "/System/Library/Fonts/Helvetica.ttc"]
    lista = candidatos_bold if negrito else candidatos_normal
    for path in lista:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, tamanho)
            except Exception:
                pass
    return ImageFont.load_default()


def _gradiente_inferior(img: Image.Image, altura_pct: float = 0.35) -> Image.Image:
    """Aplica gradiente escuro no rodapé para garantir legibilidade."""
    img = img.convert("RGBA")
    w, h = img.size
    grad_h = int(h * altura_pct)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    for i in range(grad_h):
        alpha = int(200 * (i / grad_h))          # 0 → 200 (quase 80% opaco)
        y     = h - grad_h + i
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

    return Image.alpha_composite(img, overlay).convert("RGB")


def renderizar_imagem(
    image_pil: Image.Image,
    payload: dict,
) -> Image.Image:
    """
    Renderiza texto (produto + preço) sobre a imagem usando Pillow.
    Espelha a lógica do renderCanvas.js para consistência backend/frontend.

    Args:
        image_pil: imagem PIL original (após crop de formato se necessário)
        payload:   dict montado por montar_payload_render()
    """
    # --- Crop por formato ---
    formato = payload.get("formato", "orig")
    img     = _aplicar_crop(image_pil, formato)
    w, h    = img.size

    # --- Gradiente inferior ---
    img = _gradiente_inferior(img)
    img = img.convert("RGBA")

    # --- Zona e box de texto ---
    zona = payload.get("zona_selecionada")
    if zona and zona.get("box_original"):
        bx, by, bw, bh = zona["box_original"]
    else:
        # Fallback geométrico: faixa inferior 30%
        bh = int(h * 0.30)
        bx, by, bw = 0, h - bh, w

    # --- Tamanhos de fonte proporcionais ---
    nome_size  = max(18, int(w * 0.038))
    preco_size = max(24, int(w * 0.062))

    fonte_nome  = _carregar_fonte(nome_size,  negrito=False)
    fonte_preco = _carregar_fonte(preco_size, negrito=True)

    cor_rgb = _hex_to_rgb(payload.get("cor_texto", "#FFFFFF"))

    # --- Layer de texto ---
    txt_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw      = ImageDraw.Draw(txt_layer)

    pad_x   = int(bw * 0.06)
    pad_y   = int(bh * 0.12)
    gap     = int(nome_size * 0.6)

    texto_x       = bx + pad_x
    texto_nome_y  = by + pad_y
    texto_preco_y = texto_nome_y + nome_size + gap

    detalhes = payload.get("detalhes", "")
    preco    = payload.get("preco", "")

    # Sombra sutil
    sombra = (0, 0, 0, 160)
    if detalhes:
        draw.text((texto_x + 1, texto_nome_y + 1),  detalhes, font=fonte_nome,  fill=sombra)
        draw.text((texto_x,     texto_nome_y),       detalhes, font=fonte_nome,  fill=(*cor_rgb, 255))

    if preco:
        draw.text((texto_x + 2, texto_preco_y + 2),  preco, font=fonte_preco, fill=sombra)
        draw.text((texto_x,     texto_preco_y),       preco, font=fonte_preco, fill=(*cor_rgb, 255))

    resultado = Image.alpha_composite(img, txt_layer)
    return resultado.convert("RGB")


def _aplicar_crop(img: Image.Image, formato: str) -> Image.Image:
    """Espelha o switch de formato do renderCanvas.js."""
    ow, oh = img.size

    if formato == "1:1":
        lado = min(ow, oh)
        sx   = (ow - lado) // 2
        sy   = (oh - lado) // 2
        img  = img.crop((sx, sy, sx + lado, sy + lado))
        return img.resize((1080, 1080), Image.LANCZOS)

    if formato == "story":
        alvo = 9 / 16
        atual = ow / oh
        if atual > alvo:
            nw = int(oh * alvo); sx = (ow - nw) // 2
            img = img.crop((sx, 0, sx + nw, oh))
        else:
            nh = int(ow / alvo); sy = (oh - nh) // 2
            img = img.crop((0, sy, ow, sy + nh))
        return img.resize((1080, 1920), Image.LANCZOS)

    if formato == "4:5":
        alvo = 4 / 5
        atual = ow / oh
        if atual > alvo:
            nw = int(oh * alvo); sx = (ow - nw) // 2
            img = img.crop((sx, 0, sx + nw, oh))
        else:
            nh = int(ow / alvo); sy = (oh - nh) // 2
            img = img.crop((0, sy, ow, sy + nh))
        return img.resize((1080, 1350), Image.LANCZOS)

    # orig — limitar a 2048
    max_s = 2048
    if ow > max_s or oh > max_s:
        scale = min(max_s / ow, max_s / oh)
        img   = img.resize((int(ow * scale), int(oh * scale)), Image.LANCZOS)
    return img


def _salvar_imagem(img: Image.Image, prefix: str = "arte") -> str:
    """Salva JPEG em static/output/ e retorna a URL relativa."""
    nome     = f"{prefix}_{uuid.uuid4().hex[:10]}.jpg"
    caminho  = OUTPUT_DIR / nome
    img.save(str(caminho), "JPEG", quality=92, optimize=True)
    return f"/static/output/{nome}"


def _base64_para_pil(base64_str: str) -> Image.Image:
    """
    Aceita tanto 'data:image/jpeg;base64,AAA...' quanto 'AAA...' puro.
    """
    if "," in base64_str:
        base64_str = base64_str.split(",", 1)[1]
    raw = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(raw)).convert("RGB")


# ===========================================================================
# PROCESSAMENTO DE UM ITEM
# ===========================================================================

def processar_item(image_b64: str, texto: str, config: dict) -> dict:
    """
    Pipeline completo para um único item:
        base64 + texto + config → dict com URLs prontas

    Returns:
        {
          "status": "success" | "error",
          "url_resultado": str,   ← imagem com texto renderizado
          "url_fundo": str,       ← imagem sem texto (para drag de etiqueta)
          "url_etiqueta_png": None,  ← futuro: etiqueta recortada separada
          "dados_extraidos": {...},
          "topografo_meta": {...},   ← debug / log
          "tempo_ms": int,
        }
    """
    t0 = time.time()

    # 1. Decodificar imagem
    image_pil = _base64_para_pil(image_b64)

    # 2. Agente 02 — Editor (NLP)
    editor_out = processar_texto(texto)

    if not editor_out["sucesso"]:
        # LLM fallback não implementado ainda — retorna erro claro
        motivo = editor_out.get("motivo", "desconhecido")
        return {
            "status":  "error",
            "message": f"Não foi possível extrair dados do texto ({motivo}). "
                       f"Tente: 'Nome do Produto preço' ex: 'Colar Ouro 18k 320'",
        }

    # 3. Agente 01 — Topógrafo (visão computacional)
    topografo_out = chamar_topografo(image_pil)

    # 4. Bridge — montar payload para renderização
    render_payload = montar_payload_render(topografo_out, editor_out, config)

    # 5. Renderizar imagem com texto (Pillow, espelha renderCanvas.js)
    img_com_texto = renderizar_imagem(image_pil, render_payload)

    # 6. Salvar fundo limpo (sem texto) para o drag da etiqueta no frontend
    img_fundo = _aplicar_crop(image_pil, render_payload.get("formato", "orig"))
    url_fundo     = _salvar_imagem(img_fundo,     prefix="fundo")
    url_resultado = _salvar_imagem(img_com_texto, prefix="arte")

    tempo_ms = int((time.time() - t0) * 1000)

    return {
        "status":          "success",
        "url_resultado":   url_resultado,
        "url_fundo":       url_fundo,
        "url_etiqueta_png": None,          # TODO: Agente 01 real → recorte do produto
        "dados_extraidos": {
            "produto":   editor_out.get("produto"),
            "preco":     editor_out.get("preco"),
            "parcelas":  editor_out.get("parcelas"),
            "categoria": editor_out.get("categoria"),
        },
        "topografo_meta": {
            "failsafe": topografo_out.get("failsafe_triggered"),
            "zonas":    len(topografo_out.get("free_zones", [])),
        },
        "tempo_ms": tempo_ms,
    }


# ===========================================================================
# FASTAPI  (produção)
# ===========================================================================

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    app = FastAPI(
        title="Precifica.AI API",
        version="1.0.0",
        description="Backend de geração automática de artes para joalherias",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # Em produção: restringir ao domínio do frontend
        allow_methods=["POST", "GET"],
        allow_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    # --- Pydantic Models ---

    class ItemPayload(BaseModel):
        image: str          # base64 (com ou sem prefixo data:)
        texto: str

    class ConfigPayload(BaseModel):
        formato:    str = "original"
        paleta:     str = "classico"
        modo_preco: str = "padrao"

    class BatchPayload(BaseModel):
        itens:  list[ItemPayload]
        config: ConfigPayload = ConfigPayload()

    # --- Rotas ---

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "1.0.0"}

    @app.post("/api/processar/batch")
    def processar_batch_endpoint(payload: BatchPayload):
        if not payload.itens:
            raise HTTPException(status_code=400, detail="Nenhum item enviado.")
        if len(payload.itens) > 20:
            raise HTTPException(status_code=400, detail="Máximo de 20 itens por batch.")

        config_dict = payload.config.model_dump()
        resultados  = []
        erros       = 0

        for item in payload.itens:
            try:
                res = processar_item(item.image, item.texto, config_dict)
            except Exception as e:
                traceback.print_exc()
                res = {"status": "error", "message": str(e)}

            if res["status"] != "success":
                erros += 1
            resultados.append(res)

        status_geral = (
            "success" if erros == 0
            else "partial" if erros < len(resultados)
            else "error"
        )

        return {"status": status_geral, "resultados": resultados}

    USANDO_FASTAPI = True

except ImportError:
    USANDO_FASTAPI = False


# ===========================================================================
# FLASK  (fallback dev — `python main.py`)
# ===========================================================================

if not USANDO_FASTAPI:
    from flask import Flask, request, jsonify, send_from_directory
    from flask import Response

    flask_app = Flask(__name__, static_folder=str(BASE_DIR / "static"))

    @flask_app.after_request
    def _cors(resp):
        resp.headers["Access-Control-Allow-Origin"]  = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return resp

    @flask_app.route("/health")
    def health_flask():
        return jsonify({"status": "ok", "runner": "flask-dev"})

    @flask_app.route("/static/output/<path:fname>")
    def serve_output(fname):
        return send_from_directory(str(OUTPUT_DIR), fname)

    @flask_app.route("/api/processar/batch", methods=["POST", "OPTIONS"])
    def processar_batch_flask():
        if request.method == "OPTIONS":
            return Response(status=200)

        data = request.get_json(force=True)

        itens  = data.get("itens", [])
        config = data.get("config", {})

        if not itens:
            return jsonify({"status": "error", "message": "Nenhum item enviado."}), 400
        if len(itens) > 20:
            return jsonify({"status": "error", "message": "Máximo 20 itens."}), 400

        resultados = []
        erros      = 0

        for item in itens:
            try:
                res = processar_item(item["image"], item["texto"], config)
            except Exception as e:
                traceback.print_exc()
                res = {"status": "error", "message": str(e)}

            if res["status"] != "success":
                erros += 1
            resultados.append(res)

        status_geral = (
            "success" if erros == 0
            else "partial" if erros < len(resultados)
            else "error"
        )

        return jsonify({"status": status_geral, "resultados": resultados})

    def main():
        print("=" * 55)
        print("  Precifica.AI — Dev Server (Flask)")
        print("  http://localhost:8000")
        print("  Endpoint: POST /api/processar/batch")
        print("  Health:   GET  /health")
        print("  Saídas:   static/output/")
        print("=" * 55)
        flask_app.run(host="0.0.0.0", port=8000, debug=True)

    if __name__ == "__main__":
        main()


# ===========================================================================
# TESTES DE INTEGRAÇÃO EMBUTIDOS
# Rode: python main.py --test
# ===========================================================================

def _run_integration_tests():
    """
    Simula uma chamada batch completa sem servidor HTTP.
    Usa uma imagem sintética (RGB sólida) para testar o pipeline ponta a ponta.
    """
    print("\\n" + "=" * 55)
    print("  Testes de Integração — Precifica.AI Backend")
    print("=" * 55 + "\\n")

    # Gerar imagem sintética 800×1000 (portrait)
    img_teste = Image.new("RGB", (800, 1000), color=(30, 25, 15))
    buf       = io.BytesIO()
    img_teste.save(buf, format="JPEG")
    b64       = base64.b64encode(buf.getvalue()).decode()

    casos = [
        {
            "desc":   "Caso 1: texto simples com preço inteiro",
            "texto":  "colar verde 89",
            "config": {"formato": "original", "paleta": "classico", "modo_preco": "padrao"},
            "espera": {"produto_contains": "Colar", "preco_contains": "89"},
        },
        {
            "desc":   "Caso 2: abreviação + unidade de medida (bug clássico)",
            "texto":  "brinco 3cm prata 145",
            "config": {"formato": "feed_quadrado", "paleta": "classico", "modo_preco": "padrao"},
            "espera": {"produto_contains": "Brinco", "preco_contains": "145"},
        },
        {
            "desc":   "Caso 3: milhar + formato story",
            "texto":  "anel aliança ouro 18k 1.200",
            "config": {"formato": "stories", "paleta": "luxo", "modo_preco": "padrao"},
            "espera": {"produto_contains": "Anel", "preco_contains": "1.200"},
        },
        {
            "desc":   "Caso 4: texto vazio → deve retornar error",
            "texto":  "",
            "config": {"formato": "original", "paleta": "classico", "modo_preco": "padrao"},
            "espera": {"status": "error"},
        },
        {
            "desc":   "Caso 5: base64 com prefixo data:image (como o browser envia)",
            "texto":  "pulseira prata 89,90",
            "config": {"formato": "original", "paleta": "classico", "modo_preco": "padrao"},
            "b64_prefixo": True,
            "espera": {"produto_contains": "Pulseira", "preco_contains": "89"},
        },
    ]

    passaram = 0
    for caso in casos:
        print(f"  {caso['desc']}")
        img_b64 = f"data:image/jpeg;base64,{b64}" if caso.get("b64_prefixo") else b64

        try:
            res = processar_item(img_b64, caso["texto"], caso["config"])
        except Exception as e:
            res = {"status": "error", "message": str(e)}

        esp = caso["espera"]
        ok  = True

        if "status" in esp:
            ok = res["status"] == esp["status"]
        else:
            if res["status"] != "success":
                ok = False
                print(f"    ❌ status={res['status']} — {res.get('message')}")
            else:
                dados = res.get("dados_extraidos", {})
                if "produto_contains" in esp:
                    if esp["produto_contains"] not in (dados.get("produto") or ""):
                        ok = False
                        print(f"    ❌ produto '{dados.get('produto')}' não contém '{esp['produto_contains']}'")
                if "preco_contains" in esp:
                    if esp["preco_contains"] not in (dados.get("preco") or ""):
                        ok = False
                        print(f"    ❌ preço '{dados.get('preco')}' não contém '{esp['preco_contains']}'")

        if ok:
            passaram += 1
            extra = ""
            if res.get("status") == "success":
                extra = (f"→ {res['dados_extraidos']['produto']} | "
                         f"{res['dados_extraidos']['preco']} | "
                         f"{res.get('tempo_ms')}ms | "
                         f"failsafe={res['topografo_meta']['failsafe']}")
            print(f"    ✅ {extra}")
        print()

    print(f"  Resultado: {passaram}/{len(casos)} passaram")

    # Verificar arquivos gerados
    arquivos = list(OUTPUT_DIR.glob("*.jpg"))
    print(f"  Arquivos gerados em static/output/: {len(arquivos)}")
    for f in arquivos[-3:]:  # Mostrar últimos 3
        size_kb = f.stat().st_size // 1024
        print(f"    {f.name} ({size_kb} KB)")

    print("\\n" + "=" * 55)
    return passaram == len(casos)


if __name__ == "__main__" and "--test" in sys.argv:
    ok = _run_integration_tests()
    sys.exit(0 if ok else 1)
