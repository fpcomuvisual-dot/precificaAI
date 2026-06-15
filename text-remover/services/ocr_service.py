import easyocr
import numpy as np
import cv2

# Mantive gpu=False para garantir compatibilidade
reader = easyocr.Reader(['pt', 'en'], gpu=False) 

def detect_text(image_np: np.ndarray):
    # Otimização: paragraph=True ajuda a agrupar textos próximos
    # Retorna uma lista de [bbox, text] (apenas 2 valores, sem probabilidade explícita para o grupo)
    result = reader.readtext(image_np, detail=1, paragraph=True)
    boxes = []
    
    for item in result:
        # EasyOCR com paragraph=True retorna apenas (bbox, text)
        if len(item) == 3:
             bbox, text, prob = item
             if prob < 0.4: continue
        else:
             bbox, text = item
             # Sem probabilidade individual no modo parágrafo, assumimos válido
        
        # Converte os pontos do polígono para um retângulo simples (x, y, w, h)
        pts = np.array(bbox, dtype=np.int32)
        x, y, w, h = cv2.boundingRect(pts)
        
        # Padding inicial MÍNIMO apenas para garantir que a letra inteira tá dentro.
        # A mágica da expansão vai ser feita no mask_service.py
        pad_x = 2
        pad_y = 2
        boxes.append([
            max(0, x - pad_x), 
            max(0, y - pad_y), 
            w + (pad_x*2), 
            h + (pad_y*2)
        ])
    
    return boxes
