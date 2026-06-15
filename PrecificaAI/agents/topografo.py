import numpy as np
from PIL import Image
from rembg import remove
import io

class Topografo:
    def __init__(self):
        # Configuração interna: tamanho alvo para padronização
        self.target_size = (1024, 1024)

    def letterbox_image(self, image):
        """
        Redimensiona mantendo a proporção e adiciona padding INTELIGENTE.
        CRUCIAL: Detecta cor da borda da imagem original para padding natural.
        """
        iw, ih = image.size
        w, h = self.target_size
        scale = min(w/iw, h/ih)
        nw = int(iw * scale)
        nh = int(ih * scale)

        image_resized = image.resize((nw, nh), Image.Resampling.LANCZOS)
        
        # ========================================
        # FIX: Detectar cor da borda da imagem ORIGINAL
        # e usar como padding, em vez de cinza fixo
        # ========================================
        img_array = np.array(image)
        amostra = 15  # pixels de borda
        h_img, w_img = img_array.shape[:2]
        
        if h_img > amostra * 2 and w_img > amostra * 2:
            bordas = np.concatenate([
                img_array[:amostra, :, :].reshape(-1, 3),
                img_array[-amostra:, :, :].reshape(-1, 3),
                img_array[:, :amostra, :].reshape(-1, 3),
                img_array[:, -amostra:, :].reshape(-1, 3),
            ])
            cor_padding = tuple(int(x) for x in np.median(bordas, axis=0))
        else:
            cor_padding = (255, 255, 255)  # Fallback branco
        
        new_image = Image.new('RGB', self.target_size, cor_padding)
        
        pad_x = (w - nw) // 2
        pad_y = (h - nh) // 2
        
        new_image.paste(image_resized, (pad_x, pad_y))
        return new_image, scale, (pad_x, pad_y)

    def analisar_contraste(self, image, rect):
        """
        Analisa a luminância média da área onde o texto vai ficar.
        Retorna: 'light' (texto branco) ou 'dark' (texto preto).
        """
        x, y, w, h = rect
        # Garante coordenadas seguras
        x, y = max(0, int(x)), max(0, int(y))
        w, h = min(int(w), image.width - x), min(int(h), image.height - y)

        if w <= 0 or h <= 0: return 'light'

        crop = image.crop((x, y, x+w, y+h)).convert('L')
        avg_luminance = np.mean(np.array(crop))

        # Se fundo escuro (<128), usa texto claro. Senão, texto escuro.
        return 'light' if avg_luminance < 128 else 'dark'

    def analisar_terreno(self, image_path):
        """
        Pipeline Limpo e Direto:
        1. Carrega Imagem
        2. Letterbox (Geometria)
        3. Rembg (Máscara Pixel-Perfeita)
        """
        try:
            original_img = Image.open(image_path).convert("RGB")
            
            # 1. Geometria (Letterboxing)
            lbox_img, scale, padding = self.letterbox_image(original_img)
            
            # 2. Inteligência (Rembg) - A Mágica acontece aqui
            # remove(..., only_mask=True) retorna imagem onde Branco (255) = Objeto, Preto (0) = Fundo
            mask_img = remove(lbox_img, only_mask=True)
            
            # Converter para NumPy (0 e 1) para facilitar a matemática do Diagramador
            # Normalizamos: 1 = Joia (Proibido), 0 = Fundo (Livre)
            mask_arr = np.array(mask_img)
            mask_binaria = (mask_arr > 0).astype(np.uint8)
            
            # ===== FIX: Analisar contraste da zona de texto =====
            zona_texto_rect = (0, int(lbox_img.height * 0.75), 
                              lbox_img.width, int(lbox_img.height * 0.25))
            analise_cor = self.analisar_contraste(lbox_img, zona_texto_rect)
            # ===== FIM DO FIX =====

            return {
                "mask": mask_binaria,
                "width": 1024,
                "height": 1024,
                "scale_info": {
                    "scale": scale,
                    "padding": padding,
                    "original_size": original_img.size
                },
                # MELHORIA: Retornar a imagem processada para evitar reabertura e desalinhamento no Diagramador
                "imagem_processada": lbox_img, 
                "analise_cor": analise_cor,
                "metodo": "rembg_pixel_perfect"
            }

        except Exception as e:
            print(f"[ERRO] Erro Critico no Topografo: {e}")
            # Fallback de emergência (retorna tudo livre mas com aviso)
            return {
                "mask": np.zeros((1024, 1024), dtype=np.uint8),
                "width": 1024, "height": 1024,
                "imagem_processada": Image.open(image_path).resize((1024,1024)),
                "analise_cor": "light",  # Fallback seguro
                "erro": str(e)
            }

    def preparar_imagem_preview(self, image_path, remover_fundo=False):
        """
        Prepara imagem para preview (resize 1024x1024).
        Se remover_fundo=True, aplica rembg (cuidado com pessoas!).
        Se remover_fundo=False, apenas redimensiona (modo seguro).
        """
        try:
            pil_img = Image.open(image_path).convert("RGBA")
            
            # 1. Resize / Crop quadrado inteligente
            # Por simplicidade neste MVP, vamos fazer um resize simples mantendo aspect ratio 
            # e colando em canvas quadrado branco/transparente
            target_s = 1024
            pil_img.thumbnail((target_s, target_s), Image.LANCZOS)
            
            bg = Image.new("RGBA", (target_s, target_s), (255, 255, 255, 0)) # Transparente
            
            # Centralizar
            offset = ((target_s - pil_img.width) // 2, (target_s - pil_img.height) // 2)
            bg.paste(pil_img, offset)
            
            img_final = bg
            
            # 2. Remover fundo (Opcional)
            if remover_fundo:
                # Converter para bytes de novo pq rembg pede bytes ou PIL
                # Mas rembg.remove aceita PIL direto nas versoes novas? 
                # Vamos via bytes pra garantir
                buf = io.BytesIO()
                img_final.save(buf, format="PNG")
                output = remove(buf.getvalue())
                img_final = Image.open(io.BytesIO(output)).convert("RGBA")
            
            return img_final

        except Exception as e:
            print(f"[ERRO] Falha ao preparar imagem: {e}")
            return None
