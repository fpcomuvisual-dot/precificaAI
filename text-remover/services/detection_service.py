import cv2
import numpy as np
import requests
import base64

# Configurações do seu Modelo Roboflow
API_KEY = "489WKHh72w"
MODEL_ID = "jewelry-detection-wktjn/1"
CONFIDENCE = 40  # 40% de certeza mínima

def detect_tags(image_np: np.ndarray):
    """
    Detecta etiquetas usando a API Hosted do Roboflow.
    Necessário porque o pacote local 'inference' não suporta Python 3.14 ainda.
    """
    
    # 1. Converter imagem (numpy) para JPG em memória
    success, encoded_image = cv2.imencode('.jpg', image_np)
    if not success:
        print("Erro ao codificar imagem para API.")
        return []
    
    # 2. Codificar para Base64 (formato de envio web)
    img_base64 = base64.b64encode(encoded_image).decode("ascii")
    
    # 3. Montar URL de inferência
    upload_url = "".join([
        f"https://detect.roboflow.com/{MODEL_ID}",
        f"?api_key={API_KEY}",
        f"&confidence={CONFIDENCE}"
    ])
    
    try:
        # 4. Enviar requisição POST
        response = requests.post(
            upload_url,
            data=img_base64,
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        # Levanta erro se a requisição falhar (ex: sem internet)
        response.raise_for_status()
        
        result = response.json()
        boxes = []
        
        # 5. Processar resposta da IA
        if 'predictions' in result:
            for pred in result['predictions']:
                # Roboflow retorna x,y do CENTRO.
                # Convertemos para x,y do CANTO SUPERIOR ESQUERDO para nossa máscara.
                w = int(pred['width'])
                h = int(pred['height'])
                x = int(pred['x'] - w / 2)
                y = int(pred['y'] - h / 2)
                
                # Evita coordenadas negativas
                x = max(0, x)
                y = max(0, y)
                
                boxes.append([x, y, w, h])
        
        return boxes
        
    except Exception as e:
        print(f"Erro na API do Roboflow: {e}")
        # Retorna lista vazia para o app não quebrar
        return []
