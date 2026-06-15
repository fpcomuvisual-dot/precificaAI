import os
import random
import glob
from agents.topografo import Topografo
from agents.editor import Editor
from agents.diagramador import Diagramador

def run_batch():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "input")
    output_dir = os.path.join(base_dir, "output", "batch_test")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Setup Agentes
    topografo = Topografo()
    editor = Editor()
    diagramador = Diagramador()
    
    # 2. Selecionar Imagens (10 JB, 10 X)
    # Assumindo JB = Fundo Branco, X = Modelo
    
    all_files = os.listdir(input_dir)
    jb_files = [f for f in all_files if f.lower().startswith('jb') and f.lower().endswith(('.jpg', '.jpeg'))]
    x_files = [f for f in all_files if f.lower().startswith('x') and f.lower().endswith(('.jpg', '.jpeg'))]
    
    # Pegar até 10 de cada, ou misturar tudo se não achar o padrão
    selected_files = []
    selected_files.extend(jb_files[:10])
    selected_files.extend(x_files[:10])
    
    # Se não achou prefixos, pega quaisquer 20 imagens
    if not selected_files:
        print("⚠️ Prefixos JB/X não encontrados. Pegando 20 aleatórios.")
        images = [f for f in all_files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        selected_files = images[:20]

    print(f"📸 Total de imagens selecionadas: {len(selected_files)}")
    
    # 3. Dados Fictícios para variação
    produtos_ficticios = [
        "Colar Ouro 18k Ponto de Luz R$ 299,90",
        "Brinco Argola Prata 925 R$ 89,90",
        "Anel Solitário Zircônia 12x 25,90",
        "Pulseira Riviera Diamante R$ 1.250,00",
        "Conjunto Pérola Clássico de 450 por 320",
        "Corrente Veneziana Ouro Branco 10x 49,90",
        "Piercing Pressão Rodio Negro R$ 45,00",
        "Gargantilha Choker Coração R$ 119,90",
        "Aliança Ouro 18k Par 12x 150,00",
        "Tornozeleira Prata Bali R$ 65,00"
    ]
    
    # 4. Configurações de Design (Rodízio)
    configs_design = [
        {"paleta": "classico", "formato": "original", "modo_preco": "padrao"},
        {"paleta": "moderno", "formato": "feed_quadrado", "modo_preco": "parcelado"},
        {"paleta": "jovem", "formato": "stories", "modo_preco": "ambos"},
        {"paleta": "classico", "formato": "feed_retrato", "modo_preco": "promocao"}, # Feed retrato 4:5
        {"paleta": "moderno", "formato": "stories", "modo_preco": "ambos"}
    ]

    # 5. Processamento em Lote
    for i, filename in enumerate(selected_files):
        print(f"\n--- Processando {i+1}/{len(selected_files)}: {filename} ---")
        
        # Caminhos
        input_path = os.path.join(input_dir, filename)
        
        # Escolhas aleatórias/sequenciais
        texto_raw = random.choice(produtos_ficticios)
        cfg = configs_design[i % len(configs_design)] # Alterna designs
        
        try:
            # A. Visão (Topografo)
            print("👁️  Topógrafo analisando...")
            dados_visuais = topografo.analisar_terreno(input_path)
            
            # B. Texto (Editor)
            print(f"📝 Editor lendo: '{texto_raw}'")
            dados_texto = editor.processar_texto(texto_raw)
            
            # C. Renderização (Diagramador)
            print(f"🎨 Diagramador aplicando: {cfg['paleta']} / {cfg['formato']}")
            
            nome_saida = f"result_{i:02d}_{cfg['paleta']}_{cfg['formato']}_{filename}"
            output_path = os.path.join(output_dir, nome_saida)
            
            diagramador.renderizar(
                input_path,
                dados_texto,
                output_path,
                dados_visuais,
                paleta=cfg['paleta'],
                formato=cfg['formato'],
                modo_preco=cfg['modo_preco']
            )
            print(f"✅ Salvo: {nome_saida}")
            
        except Exception as e:
            print(f"❌ Erro ao processar {filename}: {e}")

if __name__ == "__main__":
    run_batch()
