"""
PrecificaAI — API Server
Conecta o frontend aos 3 agentes de processamento.

Rodar: uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import uuid
import base64
import time
import io
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request

# ... (omitting lines for brevity)





from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from orquestrador import PipelinePrecifica
from config import settings

# Garante que as pastas necessárias existam antes de montar os StaticFiles
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
os.makedirs(settings.LOGOS_DIR, exist_ok=True)


# ============================================================
# STARTUP / SHUTDOWN
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos ao subir o servidor."""
    # Criar pastas necessárias
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(settings.LOGOS_DIR, exist_ok=True)
    
    # Inicializar pipeline (carrega Rembg model na RAM uma vez só)
    app.state.pipeline = PipelinePrecifica()
    print("[OK] PrecificaAI Server iniciado!")
    print(f"   Uploads: {settings.UPLOAD_DIR}")
    print(f"   Output:  {settings.OUTPUT_DIR}")
    print(f"   Front:   http://localhost:8000")

    yield

    print("[OK] PrecificaAI Server encerrado.")


app = FastAPI(
    title="PrecificaAI",
    description="API de automação de design para joalherias",
    version="1.1",
    lifespan=lifespan,
)

# CORS — permitir front local (dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringir ao domínio do front
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Apontar para o build de produção do React
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Servir arquivos estáticos
app.mount("/output", StaticFiles(directory=settings.OUTPUT_DIR), name="output")
# Servir pasta frontend inteira para CSS/JS internos se houver
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


# ============================================================
# MODELOS DE REQUEST/RESPONSE
# ============================================================
class ConfigProcessamento(BaseModel):
    formato: str = "original"           # original | feed_quadrado | feed_retrato | stories
    paleta: str = "classico"            # classico | moderno | jovem
    modo_preco: str = "padrao"          # padrao | parcelado | ambos | promocao

class ProcessarRequest(BaseModel):
    image: str                          # Base64 da imagem
    texto: str                          # Texto bruto ("colar ouro 89,90")
    config: Optional[ConfigProcessamento] = None

class ItemBatch(BaseModel):
    image: str                          # Base64 da imagem
    texto: str                          # Texto bruto

class BatchRequest(BaseModel):
    itens: List[ItemBatch]
    config: Optional[ConfigProcessamento] = None

class RenderizarRequest(BaseModel):
    image: str                          # Base64 da imagem
    dados_confirmados: Dict[str, Any]             # Dados editados pelo usuário
    config: Optional[ConfigProcessamento] = None

class ProcessarTextoRequest(BaseModel):
    texto: str                          # Texto bruto ("aneu de rodiu 10x 2")


# ============================================================
# ROTAS
# ============================================================

# ----------------------------------------------------------
# ROTA 1A: Preview (Limpar Fundo)
# ----------------------------------------------------------
@app.post("/api/tratar-imagem")
async def tratar_imagem(request: Request, file: UploadFile = File(...)):
    """
    Remove fundo da imagem e retorna preview em base64.
    Não salva no disco de output, apenas processa na memória.
    """
    try:
        pipeline: PipelinePrecifica = app.state.pipeline
        
        # 1. Salvar temp
        temp_id = str(uuid.uuid4())[:8]
        file_ext = os.path.splitext(file.filename)[1] or ".jpg"
        temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_preview_{temp_id}{file_ext}")
        
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
            
        # 2. Processar (Modo Seguro: SEM Remover Fundo por padrão)
        limpar = request.query_params.get('limpar_fundo', 'false').lower() == 'true'
        print(f"[PREVIEW] Preparando imagem: {temp_path} (Remover Fundo: {limpar})")
        
        # Pipeline Topografo V2
        img_limpa = pipeline.topografo.preparar_imagem_preview(temp_path, remover_fundo=limpar)
        
        # Cleanup temp
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if not img_limpa:
            return JSONResponse(status_code=500, content={"success": False, "message": "Falha ao preparar imagem."})
            
        # 3. Converter para Base64
        buffered = io.BytesIO()
        img_limpa.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # 4. Mock Boxes (Detecção de Preços)
        # O usuário espera que o sistema detecte preços.
        # Sem OCR, vamos simular (Mock) caixas na parte inferior/direita
        # Formato esperado: [[x, y, w, h], ...] (relativo à imagem 1024x1024)
        mock_boxes = [
            # [x, y, w, h]
            [700, 850, 200, 80], # Canto inferior direito (mock seguro)
            # [100, 850, 200, 80], # Canto inferior esquerdo (opcional)
        ]
        
        return {
            "success": True,
            "image_base64": img_str,
            "boxes": mock_boxes 
        }

    except Exception as e:
        print(f"Erro em /api/tratar-imagem: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})


# ----------------------------------------------------------
# ROTA 1: Processar imagem individual
# ----------------------------------------------------------

@app.post("/api/processar")
async def processar_imagem(request: ProcessarRequest):
    """
    Fluxo completo: Upload → Agente 01 → 02 → 03 → Imagem pronta.
    
    O front chama esta rota após o usuário preencher tudo e clicar "Gerar".
    Retorna os dados extraídos (para o Card de Confirmação) E a imagem.
    """
    try:
        pipeline: PipelinePrecifica = app.state.pipeline
        config = request.config or ConfigProcessamento()
        
        # 1. Decodificar imagem base64 → arquivo temporário
        img_id = str(uuid.uuid4())[:8]
        img_path = _salvar_base64(request.image, img_id)
        
        # 2. Rodar pipeline completo
        resultado = pipeline.executar(
            imagem_path=img_path,
            texto_bruto=request.texto,
            formato=config.formato,
            paleta=config.paleta,
            modo_preco=config.modo_preco,
        )
        
        if not resultado["sucesso"]:
            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "error_code": resultado.get("erro_code", "PROCESSAMENTO_FALHOU"),
                    "message": resultado.get("mensagem", "Erro ao processar imagem."),
                    "dados_parciais": resultado.get("dados_parciais"),
                }
            )
        
        # 3. Montar URL do resultado
        nome_arquivo = resultado["arquivo_saida"]
        # Assumindo que o frontend está no mesmo host
        url_resultado = f"/output/{nome_arquivo}"
        
        return {
            "status": "success",
            "url_resultado": url_resultado,
            "dados_extraidos": resultado["dados_editor"],
            "tempo_processamento_ms": resultado["tempo_ms"],
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# ----------------------------------------------------------
# ROTA 2: Processar batch (múltiplas imagens)
# ----------------------------------------------------------
@app.post("/api/processar/batch")
async def processar_batch(request: BatchRequest):
    """
    Processa múltiplas imagens de uma vez.
    Cada item tem sua própria imagem e texto.
    A config (formato, paleta, modo_preco) é compartilhada.
    """
    pipeline: PipelinePrecifica = app.state.pipeline
    config = request.config or ConfigProcessamento()
    resultados = []
    
    for i, item in enumerate(request.itens):
        try:
            img_id = f"batch_{str(uuid.uuid4())[:6]}_{i:02d}"
            img_path = _salvar_base64(item.image, img_id)
            
            resultado = pipeline.executar(
                imagem_path=img_path,
                texto_bruto=item.texto,
                formato=config.formato,
                paleta=config.paleta,
                modo_preco=config.modo_preco,
            )
            
            if resultado["sucesso"]:
                resultados.append({
                    "index": i,
                    "status": "success",
                    "url_resultado": f"/output/{resultado['arquivo_saida']}",
                    "dados_extraidos": resultado["dados_editor"],
                })
            else:
                resultados.append({
                    "index": i,
                    "status": "error",
                    "message": resultado.get("mensagem", "Falha no processamento"),
                })
        
        except Exception as e:
            resultados.append({
                "index": i,
                "status": "error",
                "message": str(e),
            })
    
    sucesso = sum(1 for r in resultados if r["status"] == "success")
    falha = len(resultados) - sucesso
    
    return {
        "status": "success" if falha == 0 else "partial",
        "resultados": resultados,
        "resumo": {
            "total": len(resultados),
            "sucesso": sucesso,
            "falha": falha,
        }
    }


# ----------------------------------------------------------
# ROTA 3: Renderizar com dados confirmados/editados
# ----------------------------------------------------------
@app.post("/api/renderizar")
async def renderizar_confirmado(request: RenderizarRequest):
    """
    Chamado APÓS o Card de Confirmação (Passo 3.5).
    O usuário pode ter editado produto/preço.
    Pula o Agente 02 — vai direto do 01 pro 03.
    """
    try:
        pipeline: PipelinePrecifica = app.state.pipeline
        config = request.config or ConfigProcessamento()
        
        img_id = str(uuid.uuid4())[:8]
        img_path = _salvar_base64(request.image, img_id)
        
        resultado = pipeline.executar_com_dados_confirmados(
            imagem_path=img_path,
            dados_confirmados=request.dados_confirmados,
            formato=config.formato,
            paleta=config.paleta,
            modo_preco=config.modo_preco,
        )
        
        if not resultado["sucesso"]:
            raise HTTPException(status_code=422, detail=resultado.get("mensagem"))
        
        return {
            "status": "success",
            "url_resultado": f"/output/{resultado['arquivo_saida']}",
            "dados_extraidos": request.dados_confirmados,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------
# ROTA 3.5: Processar texto (NLP — Agente 02 Groq isolado)
# ----------------------------------------------------------
@app.post("/api/processar-texto")
async def processar_texto_endpoint(request: ProcessarTextoRequest):
    """
    Expõe SÓ o Agente 02 (Editor / Groq Llama) — sem rodar a pipeline
    de imagem. Recebe texto bruto da vendedora e devolve os campos
    estruturados (nome / preço / parcelas) prontos pro StyleSettings.

    Rápido (<2s): reusa o Editor já carregado no singleton da pipeline.
    """
    texto = (request.texto or "").strip()
    if not texto:
        return JSONResponse(
            status_code=422,
            content={"status": "error", "motivo": "texto_vazio"},
        )

    try:
        pipeline: PipelinePrecifica = app.state.pipeline
        dados = pipeline.editor.processar_texto(texto)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "motivo": "erro_interno", "detalhe": str(e)},
        )

    if not dados.get("sucesso"):
        return JSONResponse(
            status_code=422,
            content={"status": "error", "motivo": dados.get("motivo", "texto_invalido")},
        )

    # Normaliza pro triplo limpo que o front consome. O Editor já entrega
    # preco_valor (total) e parcelas {quantidade, valor_parcela}.
    parcelas = dados.get("parcelas") or {}
    qtd = parcelas.get("quantidade")
    valp = parcelas.get("valor_parcela")

    return {
        "status": "success",
        "nome": dados.get("produto", ""),
        "preco": _formatar_preco_brl(dados.get("preco_valor")),
        "parcelas": _formatar_parcelas(qtd, valp),
        "modo": dados.get("modo_detectado"),
        "raw": dados,
    }


# ----------------------------------------------------------
# ROTA 4: Upload de logo (futuro)
# ----------------------------------------------------------
@app.post("/api/logo/upload")
async def upload_logo(file: UploadFile = File(...)):
    """
    Recebe logo do cliente, remove fundo se necessário,
    salva como PNG transparente.
    """
    # TODO: Fase 1.2
    # 1. Salvar arquivo
    # 2. Se não for PNG com alpha, rodar Rembg
    # 3. Retornar URL do logo processado
    return {"status": "not_implemented", "message": "Logo será implementado na fase 1.2"}


# ----------------------------------------------------------
# ROTA 5: Health check
# ----------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.1",
        "agentes": {
            "topografo": "ready",
            "editor": "ready",
            "diagramador": "ready",
        }
    }


# ----------------------------------------------------------
# ROTA 6: Servir o front-end (index)
# ----------------------------------------------------------
@app.get("/")
async def serve_frontend():
    # Procura index.html na pasta frontend
    path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "Bem vindo ao PrecificaAI API. Front-end não encontrado em /frontend/index.html"}


# ============================================================
# HELPERS
# ============================================================
def _formatar_preco_brl(valor) -> str:
    """89.0 -> 'R$ 89,00' | 1450.0 -> 'R$ 1.450,00' | None/0 -> 'Consulte'."""
    if valor is None:
        return "Consulte"
    valor = float(valor)
    if valor <= 0:
        return "Consulte"
    inteiro = int(valor)
    centavos = int(round((valor - inteiro) * 100))
    if centavos == 100:  # arredondamento de borda (ex: 19.999)
        inteiro += 1
        centavos = 0
    if inteiro >= 1000:
        milhar = f"{inteiro:,}".replace(",", ".")
        return f"R$ {milhar},{centavos:02d}"
    return f"R$ {inteiro},{centavos:02d}"


def _formatar_parcelas(quantidade, valor_parcela) -> str:
    """10, 2.0 -> '10x R$ 2,00' | faltando algo -> ''."""
    if not quantidade or not valor_parcela:
        return ""
    valor_fmt = f"{float(valor_parcela):.2f}".replace(".", ",")
    return f"{int(quantidade)}x R$ {valor_fmt}"


def _salvar_base64(base64_str: str, nome_id: str) -> str:
    """
    Decodifica base64 e salva como arquivo temporário.
    Retorna o path do arquivo salvo.
    """
    # Remover header "data:image/jpeg;base64," se presente
    if "," in base64_str:
        base64_str = base64_str.split(",", 1)[1]
    
    # Remover espaços em branco ou newlines que podem vir no JSON
    base64_str = base64_str.strip()
    
    try:
        img_bytes = base64.b64decode(base64_str)
    except Exception as e:
        raise ValueError(f"Base64 inválido: {e}")
    
    # Detectar extensão pelo magic number
    if img_bytes[:3] == b'\xff\xd8\xff':
        ext = ".jpg"
    elif img_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        ext = ".png"
    else:
        ext = ".jpg"  # Fallback
    
    filepath = os.path.join(settings.UPLOAD_DIR, f"{nome_id}{ext}")
    with open(filepath, "wb") as f:
        f.write(img_bytes)
    
    return filepath

if __name__ == "__main__":
    import uvicorn
    # Rodar servidor de desenvolvimento
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
