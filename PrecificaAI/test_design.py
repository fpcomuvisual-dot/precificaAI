import os
from PIL import Image
from agents.topografo import Topografo
from agents.editor import Editor
from agents.diagramador import Diagramador

def run_test():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_imagem = os.path.join(base_dir, "input", "teste_joia.jpg")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Setup
    topografo = Topografo()
    editor = Editor()
    diagramador = Diagramador()
    
    # 2. Processamento Único (Pesado)
    print("🧠 Processando Imagem e Texto...")
    dados_visuais = topografo.analisar_terreno(input_imagem)
    dados_texto = editor.processar_texto("Promoção Colar Ouro 18k com Zircônia de 250 por 189,90 em 10x sem juros")
    
    # 3. Renderização Múltipla (Leve)
    configs = [
        {"paleta": "classico", "formato": "original", "modo_preco": "padrao", "nome": "1_classico_orig.jpg"},
        {"paleta": "moderno", "formato": "feed_quadrado", "modo_preco": "parcelado", "nome": "2_moderno_feed.jpg"},
        {"paleta": "jovem", "formato": "stories", "modo_preco": "ambos", "nome": "3_jovem_stories.jpg"},
    ]
    
    for cfg in configs:
        print(f"🎨 Renderizando: {cfg['nome']} ({cfg['paleta']} / {cfg['formato']})...")
        out_path = os.path.join(output_dir, cfg['nome'])
        diagramador.renderizar(
            input_imagem, 
            dados_texto, 
            out_path, 
            dados_visuais,
            paleta=cfg['paleta'],
            formato=cfg['formato'],
            modo_preco=cfg['modo_preco']
        )
        print(f"✅ Salvo em: {out_path}")

if __name__ == "__main__":
    run_test()
