from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
import base64
from io import BytesIO
from PIL import Image
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# from services.ocr_service import detect_text
from services.detection_service import detect_tags
from services.mask_service import create_mask
from services.inpainting_service import remove_text_with_lama

app = FastAPI(title="Text Remover - Microsserviço de Visão")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=4)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Text Remover - Visão Computacional</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #6366f1;
                --primary-hover: #4f46e5;
                --bg: #0f172a;
                --card-bg: #1e293b;
                --text: #f8fafc;
                --text-secondary: #94a3b8;
            }
            body {
                font-family: 'Inter', sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
            }
            h1 {
                margin: 2rem 0;
                font-size: 2.5rem;
                background: linear-gradient(to right, #818cf8, #c084fc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .container {
                width: 90%;
                max-width: 1200px;
                display: grid;
                grid-template-columns: 1fr;
                gap: 2rem;
            }
            @media (min-width: 768px) {
                .container {
                    grid-template-columns: 1fr 1fr;
                }
            }
            .card {
                background-color: var(--card-bg);
                border-radius: 1rem;
                padding: 1.5rem;
                box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 400px;
                position: relative;
            }
            .upload-area {
                width: 100%;
                height: 300px;
                border: 2px dashed var(--text-secondary);
                border-radius: 0.5rem;
                display: flex;
                justify-content: center;
                align-items: center;
                cursor: pointer;
                transition: all 0.2s;
                position: relative;
                overflow: hidden;
            }
            .upload-area:hover {
                border-color: var(--primary);
                background-color: rgba(99, 102, 241, 0.1);
            }
            .upload-area img {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
                z-index: 2;
            }
            .upload-msg {
                position: absolute;
                z-index: 1;
                color: var(--text-secondary);
                text-align: center;
            }
            .btn {
                margin-top: 1.5rem;
                background-color: var(--primary);
                color: white;
                border: none;
                padding: 0.75rem 2rem;
                border-radius: 0.5rem;
                font-weight: 600;
                cursor: pointer;
                transition: background-color 0.2s;
                font-size: 1rem;
            }
            .btn:hover {
                background-color: var(--primary-hover);
            }
            .btn:disabled {
                background-color: var(--text-secondary);
                cursor: not-allowed;
            }
            .result-container {
                width: 100%;
                height: 300px;
                border-radius: 0.5rem;
                background-color: rgba(0,0,0,0.2);
                display: flex;
                justify-content: center;
                align-items: center;
                overflow: hidden;
            }
            .result-container img {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }
            .loader {
                border: 4px solid var(--card-bg);
                border-top: 4px solid var(--primary);
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                display: none;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .stats {
                margin-top: 1rem;
                color: var(--text-secondary);
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <h1>✨ Text Remover AI</h1>
        
        <div class="container">
            <div class="card">
                <h2>Original</h2>
                <input type="file" id="fileInput" accept="image/*" style="display: none">
                <div class="upload-area" id="dropZone">
                    <div class="upload-msg">
                        <svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="margin-bottom: 0.5rem">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                        </svg>
                        <br>
                        Clique ou arraste uma imagem aqui
                    </div>
                    <img id="preview" style="display: none">
                </div>
                <button class="btn" id="processBtn" disabled>Remover Texto 🚀</button>
            </div>

            <div class="card">
                <h2>Resultado</h2>
                <div class="result-container" id="resultArea">
                    <div class="loader" id="loader"></div>
                    <img id="resultImage" style="display: none">
                    <p id="placeholderText" style="color: var(--text-secondary)">Aguardando processamento...</p>
                </div>
                <div class="stats" id="stats"></div>
                <a id="downloadBtn" class="btn" style="display: none; text-decoration: none; text-align: center" download="limpa.png">Baixar Imagem</a>
            </div>
        </div>

        <script>
            const dropZone = document.getElementById('dropZone');
            const fileInput = document.getElementById('fileInput');
            const preview = document.getElementById('preview');
            const processBtn = document.getElementById('processBtn');
            const resultImage = document.getElementById('resultImage');
            const loader = document.getElementById('loader');
            const placeholderText = document.getElementById('placeholderText');
            const stats = document.getElementById('stats');
            const downloadBtn = document.getElementById('downloadBtn');

            let currentFile = null;

            dropZone.addEventListener('click', () => fileInput.click());

            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = 'var(--primary)';
            });

            dropZone.addEventListener('dragleave', () => {
                dropZone.style.borderColor = 'var(--text-secondary)';
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = 'var(--text-secondary)';
                if (e.dataTransfer.files.length) {
                    handleFile(e.dataTransfer.files[0]);
                }
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length) {
                    handleFile(e.target.files[0]);
                }
            });

            function handleFile(file) {
                if (!file.type.startsWith('image/')) {
                    alert('Por favor, envie uma imagem.');
                    return;
                }
                currentFile = file;
                const reader = new FileReader();
                reader.onload = (e) => {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                    document.querySelector('.upload-msg').style.display = 'none';
                    processBtn.disabled = false;
                };
                reader.readAsDataURL(file);
            }

            processBtn.addEventListener('click', async () => {
                if (!currentFile) return;

                // UI Reset
                processBtn.disabled = true;
                resultImage.style.display = 'none';
                placeholderText.style.display = 'none';
                downloadBtn.style.display = 'none';
                loader.style.display = 'block';
                stats.textContent = 'Processando... (pode levar alguns segundos)';

                const formData = new FormData();
                formData.append('file', currentFile);

                try {
                    const response = await fetch('/api/tratar-imagem', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();

                    if (data.success) {
                        resultImage.src = 'data:image/png;base64,' + data.image_base64;
                        resultImage.style.display = 'block';
                        downloadBtn.href = resultImage.src;
                        downloadBtn.style.display = 'block';
                        
                        const count = data.boxes ? data.boxes.length : 0;
                        stats.textContent = `✨ Sucesso! ${count} áreas de texto removidas.`;
                    } else {
                        stats.textContent = '⚠️ ' + (data.message || 'Erro ao processar');
                        placeholderText.style.display = 'block';
                    }
                } catch (error) {
                    console.error(error);
                    stats.textContent = '❌ Erro de conexão com o servidor.';
                    placeholderText.style.display = 'block';
                } finally {
                    loader.style.display = 'none';
                    processBtn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/api/tratar-imagem")
async def tratar_imagem(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Arquivo deve ser uma imagem")

    try:
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
        image_np = np.array(image)

        # 1. Detecção com Modelo Customizado (YOLO/Roboflow)
        # Substitui o OCR genérico por IA treinada
        # Como detect_tags agora usa requests (blocking),
        # Vamos manter no executor para não bloquear o event loop do FastAPI.
        boxes = await asyncio.get_running_loop().run_in_executor(
            executor, detect_tags, image_np
        )

        if not boxes:
            return {"message": "Nenhum texto detectado", "image": None, "boxes": []}

        # 2. Máscara
        mask = await asyncio.get_running_loop().run_in_executor(
            executor, create_mask, image_np, boxes
        )

        # 3. Inpainting com LaMa
        cleaned_np = await asyncio.get_running_loop().run_in_executor(
            executor, remove_text_with_lama, image_np, mask
        )

        # Converter pra base64
        cleaned_img = Image.fromarray(cleaned_np)
        buffered = BytesIO()
        cleaned_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return {
            "success": True,
            "image_base64": img_str,
            "boxes": boxes,  # [[x, y, w, h], ...]
            "message": f"Removidos {len(boxes)} textos"
        }

    except Exception as e:
        raise HTTPException(500, f"Erro interno: {str(e)}")
