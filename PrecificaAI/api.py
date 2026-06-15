from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
import uuid
from typing import Optional

from agents.topografo import Topografo
from agents.editor import Editor
from agents.diagramador import Diagramador

app = FastAPI(title="Precifica.AI API", version="1.0.0")

# Configurar CORS (Permitir acesso do Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja para o domínio do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Servir arquivos estáticos (para o frontend baixar as imagens)
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

# Instanciar Agentes (Singleton)
topografo = Topografo()
editor = Editor()
diagramador = Diagramador()

@app.get("/")
def read_root():
    return {"status": "online", "service": "Precifica.AI by Antigravity"}

@app.post("/processar")
async def processar_imagem(
    image: UploadFile = File(...),
    texto: str = Form(...),
    paleta: str = Form("classico"),
    formato: str = Form("original"),
    modo_preco: str = Form("padrao")
):
    try:
        # 1. Salvar imagem temporária
        image_ext = image.filename.split('.')[-1]
        temp_filename = f"{uuid.uuid4()}.{image_ext}"
        temp_path = os.path.join(TEMP_DIR, temp_filename)
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        print(f"📥 Recebido: {temp_filename} | Texto: {texto}")
        
        # 2. Agente 01: Topógrafo (Visão)
        print("👁️  Topógrafo analisando...")
        dados_visuais = topografo.analisar_terreno(temp_path)
        if "erro" in dados_visuais:
            return {"status": "error", "message": f"Erro no Topógrafo: {dados_visuais['erro']}"}

        # 3. Agente 02: Editor (NLP)
        print(f"📝 Editor processando...")
        dados_texto = editor.processar_texto(texto)
        if not dados_texto.get("sucesso"):
             return {"status": "error", "message": f"Erro no Editor: {dados_texto.get('motivo')}"}

        # 4. Agente 03: Diagramador (Layout)
        output_filename = f"result_{temp_filename}"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        print(f"🎨 Diagramador renderizando...")
        diagramador.renderizar(
            temp_path,
            dados_texto,
            output_path,
            dados_visuais,
            paleta=paleta,
            formato=formato,
            modo_preco=modo_preco
        )
        
        # Limpar temp
        os.remove(temp_path)
        
        # URL pública (assumindo localhost por enquanto)
        # O frontend usará essa URL para exibir a imagem
        img_url = f"/output/{output_filename}"
        
        return {
            "status": "success",
            "url_resultado": img_url,
            "dados_extraidos": {
                "produto": dados_texto.get("produto"),
                "preco": dados_texto.get("preco_texto"),
                "parcelas": dados_texto.get("parcelas"),
                "categoria": dados_texto.get("categoria")
            },
            "config_usada": {
                "paleta": paleta,
                "formato": formato,
                "modo_preco": modo_preco
            }
        }

    except Exception as e:
        print(f"❌ Erro Crítico API: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Rodar servidor de desenvolvimento
    uvicorn.run(app, host="0.0.0.0", port=8000)
