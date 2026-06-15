# Text Remover API

Microsserviço pra remover preços de fornecedor e devolver coordenadas pro frontend recolocar.

## Como rodar
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Primeira execução baixa o modelo LaMa (~300MB).

Teste com:
```bash
curl -X POST "http://localhost:8000/api/tratar-imagem" \
  -F "file=@/caminho/da/foto.jpg"
```

Resposta: `{ "image_base64": "...", "boxes": [[x,y,w,h], ...] }`
