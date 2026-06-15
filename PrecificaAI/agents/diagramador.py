import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# FIX 1: Importação robusta. Tenta relativo, se falhar tenta absoluto.
try:
    from .posicionamento_v3 import encontrar_melhor_posicao_v3
except ImportError:
    try:
        from posicionamento_v3 import encontrar_melhor_posicao_v3
    except ImportError:
        print("❌ CRÍTICO: posicionamento_v3.py não encontrado!")
        raise


# --- CONFIGURAÇÕES DE DESIGN (SPEC V1) ---

PALETAS = {
    "classico": {
        "titulo": {"font": "PlayfairDisplay-Regular.ttf", "fallback": "times.ttf"},
        "preco":  {"font": "Montserrat-SemiBold.ttf", "fallback": "arialbd.ttf"},
        "cores": {
            "claro": "#FFFFFF", "escuro": "#1A1A1A", "accent": "#C9A96E",
            "sombra": "#000000"
        },
        "tracking": 0,
        "metodo": "sombra"  # Drop shadow suave
    },
    "moderno": {
        "titulo": {"font": "Inter-Light.ttf", "fallback": "arial.ttf"},
        "preco":  {"font": "Inter-Bold.ttf", "fallback": "arialbd.ttf"},
        "cores": {
            "claro": "#FAFAFA", "escuro": "#2D2D2D", "accent": "#E8B4B8",
            "sombra": "#1A1A1A"
        },
        "tracking": 0,
        "metodo": "backdrop"  # Retângulo glass estilo iOS
    },
    "jovem": {
        "titulo": {"font": "BebasNeue-Regular.ttf", "fallback": "arialbd.ttf"},
        "preco":  {"font": "Montserrat-Black.ttf", "fallback": "arialbd.ttf"},
        "cores": {
            "claro": "#FFFFFF", "escuro": "#0D0D0D", "accent": "#FF6B6B",
            "sombra": "#0D0D0D"
        },
        "tracking": 0,
        "metodo": "barra"  # Barra preta semitransparente
    },
    "vogue": {
        "titulo": {"font": "arial.ttf", "fallback": "arial.ttf"},
        "preco":  {"font": "arialbd.ttf", "fallback": "arialbd.ttf"},
        "cores": {
            "claro": "#FFFFFF", "escuro": "#FFFFFF", "accent": "#FFFFFF",
            "sombra": "#000000"
        },
        "tracking": 0,
        "metodo": "sombra"  # Sombra suave, texto branco
    }
}

# --- FUNÇÕES DE TEXTO PREMIUM (SEM STROKE) ---

def desenhar_texto_premium(img, pos, texto, font, cor_texto, metodo="sombra"):
    """
    Renderiza texto com acabamento premium (SEM STROKE).
    
    Métodos:
    - "sombra": Drop shadow suave (blur gaussian)
    - "barra": Barra semitransparente atrás do texto
    - "backdrop": Retângulo arredondado translúcido (estilo iOS)
    - "caixa": Caixa sólida/translúcida atrás do texto (Estilo Joalheria)
    - "flat": Texto simples sem efeito (usado sobre caixa unificada)
    """
    if metodo == "sombra":
        return _texto_com_sombra(img, pos, texto, font, cor_texto)
    elif metodo == "barra":
        return _texto_com_barra(img, pos, texto, font, cor_texto)
    elif metodo == "backdrop":
        return _texto_com_backdrop(img, pos, texto, font, cor_texto)
    elif metodo == "caixa":
        return _texto_com_caixa(img, pos, texto, font, cor_texto)
    elif metodo == "flat":
        return _texto_flat(img, pos, texto, font, cor_texto)
    else:
        # Fallback: sombra
        return _texto_com_sombra(img, pos, texto, font, cor_texto)


def _texto_com_sombra(img, pos, texto, font, cor_texto):
    """Drop shadow suave — método mais elegante."""
    x, y = pos
    w, h = img.size
    
    # Camada de sombra (transparente)
    sombra = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_sombra = ImageDraw.Draw(sombra)
    
    # Desenhar texto da sombra (preto, deslocado 2-3px)
    offset_sombra = max(2, int(font.size * 0.04))
    draw_sombra.text(
        (x + offset_sombra, y + offset_sombra),
        texto,
        font=font,
        fill=(0, 0, 0, 160),  # Preto com 63% opacidade
    )
    
    # Blur na sombra (suaviza as bordas)
    raio_blur = max(3, int(font.size * 0.06))
    sombra = sombra.filter(ImageFilter.GaussianBlur(radius=raio_blur))
    
    # Compor sombra sobre a imagem
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img = Image.alpha_composite(img, sombra)
    
    # Desenhar texto principal (SEM STROKE)
    draw = ImageDraw.Draw(img)
    draw.text((x, y), texto, font=font, fill=cor_texto)
    
    return img


def _texto_com_barra(img, pos, texto, font, cor_texto):
    """Barra semitransparente atrás do texto."""
    x, y = pos
    w, h = img.size
    draw_temp = ImageDraw.Draw(img)
    
    # Medir texto
    bbox = draw_temp.textbbox((x, y), texto, font=font)
    text_h = bbox[3] - bbox[1]
    
    # Criar barra
    barra = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_barra = ImageDraw.Draw(barra)
    
    margem_v = int(text_h * 0.4)
    barra_y1 = y - margem_v
    barra_y2 = bbox[3] + margem_v
    
    # Barra preta com opacidade (Retângulo único = +Performance)
    draw_barra.rectangle([(0, barra_y1), (w, barra_y2)], fill=(0, 0, 0, 120))
    
    # Compor barra
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img = Image.alpha_composite(img, barra)
    
    # Texto principal (SEM STROKE)
    draw = ImageDraw.Draw(img)
    draw.text((x, y), texto, font=font, fill=cor_texto)
    
    return img


def _texto_com_backdrop(img, pos, texto, font, cor_texto):
    """Retângulo arredondado translúcido (estilo iOS)."""
    x, y = pos
    w, h = img.size
    draw_temp = ImageDraw.Draw(img)
    
    # Medir texto
    bbox = draw_temp.textbbox((x, y), texto, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Backdrop
    pad_h = int(text_h * 0.5)
    pad_w = int(text_w * 0.15)
    radius = int(text_h * 0.4)
    
    backdrop = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_bd = ImageDraw.Draw(backdrop)
    draw_bd.rounded_rectangle(
        [x - pad_w, y - pad_h, bbox[2] + pad_w, bbox[3] + pad_h],
        radius=radius,
        fill=(0, 0, 0, 80),  # 31% opacidade
    )
    
    # Blur leve no backdrop (efeito glass)
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(radius=2))
    
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img = Image.alpha_composite(img, backdrop)
    
    # Texto (SEM STROKE)
    draw = ImageDraw.Draw(img)
    draw.text((x, y), texto, font=font, fill=cor_texto)
    
    return img


def _texto_com_caixa(img, pos, texto, font, cor_texto, cor_caixa=(255, 255, 255, 230)):
    """
    Texto com caixa (box) branca atrás.
    Estilo joalheria premium — limpo, sem sombra, sem stroke.
    """
    x, y = pos
    w, h = img.size
    
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    
    draw_temp = ImageDraw.Draw(img)
    
    # Medir texto
    bbox = draw_temp.textbbox((x, y), texto, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Padding interno da caixa
    pad_h = int(text_h * 0.30)   # 30% da altura do texto
    pad_w = int(text_h * 0.40)   # 40% (mais largo para respiro)
    radius = int(text_h * 0.25)  # Cantos arredondados
    
    # Criar caixa
    caixa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_caixa = ImageDraw.Draw(caixa)
    
    draw_caixa.rounded_rectangle(
        [x - pad_w, y - pad_h, bbox[2] + pad_w, bbox[3] + pad_h],
        radius=radius,
        fill=cor_caixa,
    )
    
    # Compor caixa sobre a imagem
    img = Image.alpha_composite(img, caixa)
    
    # Texto principal (SEM sombra, SEM stroke)
    draw = ImageDraw.Draw(img)
    draw.text((x, y), texto, font=font, fill=cor_texto)
    
    return img


def _texto_flat(img, pos, texto, font, cor_texto):
    """Texto simples, sem efeitos (para usar sobre caixa unificada)."""
    draw = ImageDraw.Draw(img)
    draw.text(pos, texto, font=font, fill=cor_texto)
    return img


class Diagramador:
    def __init__(self):
        # Base Path para assets
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.fonts_dir = os.path.join(self.base_dir, "assets", "fonts")

    def _carregar_fonte(self, nome_arquivo, fallback_sys, tamanho):
        """Tenta carregar do disco, senão usa fallback do sistema"""
        path = os.path.join(self.fonts_dir, nome_arquivo)
        try:
            return ImageFont.truetype(path, size=tamanho)
        except:
            try:
                # Tenta fallback do sistema (Windows/Linux)
                return ImageFont.truetype(fallback_sys, size=tamanho)
            except:
                return ImageFont.load_default()

    def _detectar_cor_borda(self, img, amostra_px=20):
        """
        Analisa as bordas da imagem e retorna a cor predominante.
        Para fotos de fundo branco, retorna branco.
        Para fotos escuras, retorna a cor escura.
        """
        # FIX RGBA: Garante 3 canais (RGB)
        img_array = np.array(img.convert('RGB'))
        h, w = img_array.shape[:2]
        if h < amostra_px * 2 or w < amostra_px * 2:
            return (255, 255, 255) # Fallback para branco
        
        # Amostrar pixels das 4 bordas
        bordas = np.concatenate([
            img_array[:amostra_px, :, :].reshape(-1, 3),      # Topo
            img_array[-amostra_px:, :, :].reshape(-1, 3),     # Base
            img_array[:, :amostra_px, :].reshape(-1, 3),      # Esquerda
            img_array[:, -amostra_px:, :].reshape(-1, 3),     # Direita
        ])
        
        # Cor mediana (mais robusta que média contra outliers)
        cor_mediana = tuple(int(x) for x in np.median(bordas, axis=0))
        return cor_mediana

    def _converter_formato(self, img_pil, formato="original"):
        """Adaptador de formato com preenchimento AUTO (cor ou blur)"""
        w, h = img_pil.size
        
        target = None
        if formato == "feed_quadrado": target = (1080, 1080)
        elif formato == "feed_retrato": target = (1080, 1350)
        elif formato == "stories": target = (1080, 1920)
        
        if not target:
            return img_pil, (0, 0, w, h)
            
        target_w, target_h = target
        
        # ESTRATÉGIA ANTI-FAIXAS (AGRESSIVA)
        # O usuário prefere CORTAR a imagem (Crop/Cover) do que ter faixas laterais.
        
        if formato == "stories":
            # Para Stories, ser mais conservador para não estourar a imagem
            # Se a imagem for paisagem (wide), fit. Se for retrato, cover.
            is_wide = (w / h) > 1.0
            if is_wide:
                scale = min(target_w/w, target_h/h) # Fit (vai ter faixas em cima/baixo, ok)
            else:
                scale = max(target_w/w, target_h/h) # Cover (zoom para preencher)
        
        else:
            # Para Feed (Quadrado/Retrato): SEMPRE COVER (Preencher tudo)
            # Corta o excedente centralizado.
            scale = max(target_w/w, target_h/h)
            
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize com alta qualidade
        img_resized = img_pil.resize((new_w, new_h), Image.LANCZOS)
        
        # Criar canvas limpo
        bg = Image.new("RGB", (target_w, target_h), (255, 255, 255))
        
        # Centralizar (Crop Central)
        pos_x = (target_w - new_w) // 2
        pos_y = (target_h - new_h) // 2
        
        # Colar (paste recorta automaticamente o que sobra)
        bg.paste(img_resized, (pos_x, pos_y))
        
        # O offset real do conteúdo útil é a interseção do canvas com a imagem
        # Se pos_x < 0 (crop), o offset visual começa em 0
        real_x = max(0, pos_x)
        real_y = max(0, pos_y)
        real_w = min(target_w, new_w) # Largura visível
        real_h = min(target_h, new_h) # Altura visível
        
        return bg, (real_x, real_y, real_w, real_h)

    # [V1 DEAD CODE REMOVED] - encontrar_melhor_posicao e helpers deletados.
    # O sistema agora usa exclusivamente agents.posicionamento_v3

    def _ajustar_texto_na_area(self, draw, texto, fonte, largura_maxima):
        """
        Verifica se o texto cabe na largura disponível.
        Se não couber:
        1. Tenta reduzir a fonte em 10%
        2. Se ainda não couber, quebra em 2 linhas
        3. Se AINDA não couber, trunca com "..."
        
        Retorna: (texto_final, fonte_final, num_linhas)
        """
        # Medir largura do texto
        bbox = draw.textbbox((0, 0), texto, font=fonte)
        largura_texto = bbox[2] - bbox[0]
        
        if largura_texto <= largura_maxima:
            return texto, fonte, 1  # Cabe normalmente
        
        # Estratégia 1: Reduzir fonte em até 30%
        tamanho_original = fonte.size
        for reducao in [0.9, 0.85, 0.8, 0.75, 0.7]:
            novo_tamanho = int(tamanho_original * reducao)
            if novo_tamanho < 16:  # Mínimo legível
                break
            try:
                fonte_menor = ImageFont.truetype(fonte.path, novo_tamanho)
            except:
                break
            bbox = draw.textbbox((0, 0), texto, font=fonte_menor)
            if (bbox[2] - bbox[0]) <= largura_maxima:
                return texto, fonte_menor, 1
        
        # Estratégia 2: Quebrar em 2 linhas
        palavras = texto.split()
        if len(palavras) > 1:
            meio = len(palavras) // 2
            linha1 = " ".join(palavras[:meio])
            linha2 = " ".join(palavras[meio:])
            
            # Verificar se cada linha cabe
            # Usa fonte original
            bbox1 = draw.textbbox((0, 0), linha1, font=fonte)
            bbox2 = draw.textbbox((0, 0), linha2, font=fonte)
            
            larg1 = bbox1[2] - bbox1[0]
            larg2 = bbox2[2] - bbox2[0]
            
            if larg1 <= largura_maxima and larg2 <= largura_maxima:
                return f"{linha1}\n{linha2}", fonte, 2
        
        # Estratégia 3: Truncar (último recurso)
        texto_trunc = texto
        bbox = draw.textbbox((0,0), texto_trunc, font=fonte)
        l_txt = bbox[2] - bbox[0]
        while l_txt > largura_maxima and len(texto_trunc) > 5:
            texto_trunc = texto_trunc[:-2]
            bbox = draw.textbbox((0, 0), texto_trunc + "...", font=fonte)
            l_txt = bbox[2] - bbox[0]
        
        if len(texto_trunc) < len(texto):
             return texto_trunc + "...", fonte, 1
             
        return texto, fonte, 1

    def renderizar(self, image_path_original, dados_texto, output_path, dados_visuais, 
                   paleta="classico", formato="original", modo_preco=None):
        
        # 1. Preparar Canvas (Imagem Base)
        img_base = dados_visuais.get('imagem_processada')
        
        if not img_base:
            # Só abre do disco se o Topógrafo não mandou a imagem pronta
            print("⚠️ Aviso: Reabrindo imagem original (Topógrafo não enviou processada)")
            img_base = Image.open(image_path_original).convert("RGBA")

        img_final, offset_info = self._converter_formato(img_base, formato)
        w, h = img_final.size
        # Converte para RGBA para desenhar
        if img_final.mode != 'RGBA':
            img_final = img_final.convert('RGBA')
        draw = ImageDraw.Draw(img_final)

        # 2. Definir Estilo
        estilo = PALETAS.get(paleta, PALETAS["classico"])
        tracking = estilo.get("tracking", 0)
        
        # 3. Analisar Cor (Contraste) — PATCH 3A: Fix Vogue
        analise_cor = dados_visuais.get('analise_cor', 'light')
        
        if paleta == "vogue":
            # Vogue: texto SEMPRE precisa contrastar com o fundo
            if analise_cor == 'dark':
                # Fundo claro → texto escuro com sombra clara
                cor_texto = "#1A1A1A"
                cor_sombra = "#FFFFFF"
            else:
                # Fundo escuro → texto branco com sombra preta
                cor_texto = "#FFFFFF"
                cor_sombra = "#000000"
        elif formato == "original":
            if analise_cor == 'light':
                cor_texto = estilo["cores"]["claro"]
                cor_sombra = estilo["cores"]["sombra"]
            else:
                cor_texto = estilo["cores"]["escuro"]
                cor_sombra = estilo["cores"]["claro"]
        else:
            # Stories sempre branco com sombra preta (padrão legibilidade)
            cor_texto = "#FFFFFF" 
            cor_sombra = "#000000"

        # 4. Encontrar Posição — PATCH V3: Margens Invisíveis (Photoshop Style)
        padding = dados_visuais.get('scale_info', {}).get('padding', (0,0))
        mask = dados_visuais['mask'] # 1024x1024
        
        # SYSTEM V3: Positioning
        bounds, metodo_override = encontrar_melhor_posicao_v3(
             image=img_final,
             mask_produto=mask,
             w=w, h=h,
             padding_info=padding,
             formato=formato,
             formato_offset=offset_info if formato != "original" else None
        )
        
        print(f">>> [V3-ACTIVE] Override Check: {metodo_override}")
        # FORCE STRICT: Default é sombra (flutuante)
        metodo = "sombra"
        
        # Mas se o sistema pediu 'caixa' (fundo complexo), usamos caixa.
        if metodo_override == "sombra": 
             # Atualização: Se o override antigo pedia sombra, 
             # agora vamos dar UPGRADE para CAIXA BRANCA para garantir leitura.
             metodo = "caixa" 
             # Ajustar cores para caixa branca
             cor_texto = "#1A1A1A"  # Preto
             estilo["cores"]["accent"] = "#C9A96E" # Dourado mantém
        elif metodo_override:
             metodo = metodo_override
             
        x1, y1, x2, y2 = bounds
        
        # Definir largura máxima para texto 
        # PATCH V3: Margens já estão no V3, aqui zeramos para respeitar
        margem_lateral = 0 
        margem_topo = 0
        margem_base = 0
        
        # Garantir largura mínima
        max_text_width = max(200, (x2 - x1) - (margem_lateral * 2))
        
        # Ponto inicial do texto
        pos_x = x1 + margem_lateral
        pos_y = y1 + margem_topo

        # 5. Configurar Fontes (Tamanhos Relativos)
        size_titulo = int(w * 0.045)
        size_preco = int(w * 0.060)
        size_parcela = int(w * 0.035)

        font_titulo = self._carregar_fonte(estilo["titulo"]["font"], estilo["titulo"]["fallback"], size_titulo)
        font_preco = self._carregar_fonte(estilo["preco"]["font"], estilo["preco"]["fallback"], size_preco)
        font_parcela = self._carregar_fonte(estilo["preco"]["font"], estilo["preco"]["fallback"], size_parcela)

        # 6. Preparar Layout — PATCH 2B: Ler do Editor
        txt_prod_raw = dados_texto.get('produto', 'Peça Exclusiva')
        if paleta == "jovem": txt_prod_raw = txt_prod_raw.upper()
        
        txt_prod_final, font_prod_final, linhas_prod = self._ajustar_texto_na_area(
            draw, txt_prod_raw, font_titulo, max_text_width
        )
        
        # Modo vem do Editor (LLM detectou), não da config do UI
        modo = dados_texto.get('modo_detectado', modo_preco or 'padrao')
        
        # O Editor v3 já monta as linhas formatadas
        txt_preco = dados_texto.get('preco_texto', 'Consulte')
        txt_parcelas = dados_texto.get('linha_parcelas', '')
        txt_preco_antigo = dados_texto.get('linha_preco_antigo', '')

        # 7. Renderizar Sequencial (Stack Vertical) — PREMIUM TEXT
        cursor_y = pos_y
        # metodo já foi definido no bloco V3 ou defaults
        
        # -- Render Título --
        if metodo == "caixa":
            # --- RENDER UNIFICADO COM CAIXA ÚNICA ---
            
            # 1. Calcular Bounding Box Total
            draw_temp = ImageDraw.Draw(img_final)
            max_w = 0
            total_h = 0
            current_y = 0  # Relativo ao topo do bloco
            
            # Simular Título
            if linhas_prod == 2:
                for line in txt_prod_final.split('\n'):
                    lb = draw_temp.textbbox((0,0), line, font=font_prod_final)
                    max_w = max(max_w, lb[2]-lb[0])
                    total_h += int(font_prod_final.size * 1.2)
            else:
                lb = draw_temp.textbbox((0,0), txt_prod_final, font=font_prod_final)
                max_w = max(max_w, lb[2]-lb[0])
                total_h += int(font_prod_final.size * 1.2)
            
            total_h += int(size_titulo * 0.3) # Gap
            
            # Simular Preço Antigo
            if txt_preco_antigo and modo == "promocao":
                lb = draw_temp.textbbox((0,0), f"De {txt_preco_antigo}", font=font_parcela)
                max_w = max(max_w, lb[2]-lb[0])
                total_h += int(size_parcela * 1.2)
            
            # Simular Preço
            lb = draw_temp.textbbox((0,0), txt_preco, font=font_preco)
            max_w = max(max_w, lb[2]-lb[0])
            total_h += int(size_preco * 1.2)
            
            # Simular Parcelas
            if txt_parcelas:
                lb = draw_temp.textbbox((0,0), txt_parcelas, font=font_parcela)
                max_w = max(max_w, lb[2]-lb[0])
                # total_h já inclui a última linha implicitamente?
                # Não, precisamos somar a altura da parcela se ela existe.
                # O cursor avançaria mais uma vez?
                # No código original: desenha e ... fim.
                # Mas a altura da parcela conta para o box.
                total_h += int(font_parcela.size * 1.2) # Estimar altura

            # 2. Desenhar Caixa Única
            pad_h = int(total_h * 0.15)
            pad_w = int(total_h * 0.20)  # Proporcional à altura total
            radius = int(total_h * 0.05) 

            # Ajustar coordenadas da caixa
            box_x1 = pos_x - pad_w
            box_y1 = pos_y - pad_h
            box_x2 = pos_x + max_w + pad_w
            box_y2 = pos_y + total_h + pad_h
            
            # Desenhar Retângulo Arredondado
            camada_box = Image.new("RGBA", (w, h), (0,0,0,0))
            draw_box = ImageDraw.Draw(camada_box)
            draw_box.rounded_rectangle(
                [box_x1, box_y1, box_x2, box_y2],
                radius=radius,
                fill=(255, 255, 255, 230) # Branco padrão
            )
            
            # Compor
            if img_final.mode != "RGBA": img_final = img_final.convert("RGBA")
            img_final = Image.alpha_composite(img_final, camada_box)
            
            # 3. Mudar modo para 'flat' (texto simples sobre a caixa)
            metodo = "flat"

        # -- Render Título --
        if linhas_prod == 2:
            partes = txt_prod_final.split('\n')
            for p in partes:
                img_final = desenhar_texto_premium(img_final, (pos_x, cursor_y), p, font_prod_final, cor_texto, metodo)
                cursor_y += int(font_prod_final.size * 1.2)
        else:
            img_final = desenhar_texto_premium(img_final, (pos_x, cursor_y), txt_prod_final, font_prod_final, cor_texto, metodo)
            cursor_y += int(font_prod_final.size * 1.2)

        cursor_y += int(size_titulo * 0.3) # Gap
        
        # -- PATCH 3D: Render Preço Antigo (se promoção) --
        if txt_preco_antigo and modo == "promocao":
            # Renderizar com risco (strikethrough)
            img_final = desenhar_texto_premium(img_final, (pos_x, cursor_y), f"De {txt_preco_antigo}", 
                                               font_parcela, "#888888", metodo)
            # Desenhar linha riscando
            draw_temp = ImageDraw.Draw(img_final)
            bbox = draw_temp.textbbox((pos_x, cursor_y), f"De {txt_preco_antigo}", font=font_parcela)
            y_meio = (bbox[1] + bbox[3]) // 2
            draw_temp.line([(bbox[0], y_meio), (bbox[2], y_meio)], fill="#888888", width=2)
            cursor_y += int(size_parcela * 1.2)
        
        # -- Render Preço Principal --
        # Se for flat (caixa branca), manter contraste. Ouro ou Preto?
        cor_preco = estilo["cores"]["accent"]
        img_final = desenhar_texto_premium(img_final, (pos_x, cursor_y), txt_preco, font_preco, cor_preco, metodo)
        cursor_y += int(size_preco * 1.2)
        
        # -- PATCH 3D: Render Parcelas (se modo "ambos") --
        if txt_parcelas:
            img_final = desenhar_texto_premium(img_final, (pos_x, cursor_y), txt_parcelas, font_parcela, cor_texto, metodo)

        img_final = img_final.convert("RGB")
        img_final.save(output_path)
        return output_path
