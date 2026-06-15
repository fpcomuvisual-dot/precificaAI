import cv2
import numpy as np

def create_mask(image_np: np.ndarray, boxes: list) -> np.ndarray:
    """
    Cria uma máscara binária baseada nas coordenadas PRECISAS da IA.
    Como o modelo YOLO já detecta a etiqueta inteira (e não só letras),
    não precisamos de expansões grandes.
    """
    h_img, w_img = image_np.shape[:2]
    mask = np.zeros((h_img, w_img), dtype=np.uint8)

    if not boxes:
        return mask

    for box in boxes:
        x, y, bw, bh = box
        
        # Converte para int apenas por garantia
        x, y, bw, bh = int(x), int(y), int(bw), int(bh)

        # Padding MÍNIMO: A IA já encontrou a etiqueta.
        # Damos apenas 8 pixels de sobra para garantir que a borda suma.
        pad = 8 
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(w_img, x + bw + pad)
        y2 = min(h_img, y + bh + pad)

        # Desenha RETÂNGULO BRANCO SÓLIDO
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, thickness=-1)

    # SUAVIZAÇÃO PARA O LAMA
    # Uma máscara dura cria 'halos'. Uma máscara suave ajuda o LaMa a misturar.
    
    # Arredonda levemente os cantos (muito bom para joias)
    kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.dilate(mask, kernel_ellipse, iterations=1)
    
    # Blur nas bordas
    mask = cv2.GaussianBlur(mask, (21, 21), 0)
    
    # Binarização leve para manter a forma mas limpar ruídos
    _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    
    # Segundo blur muito leve para anti-aliasing final
    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    return mask
