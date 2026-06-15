import os
from agents.topografo import Topografo
from agents.editor import Editor
from agents.diagramador import Diagramador

# Teste com a paleta Vogue (estilo clean)
topografo = Topografo()
editor = Editor()
diagramador = Diagramador()

# Seleciona uma imagem de teste
input_dir = "X:/Dev/TEXTOJOIA/Antigravity/PrecificaAI/input"
test_images = [f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

if test_images:
    test_img = os.path.join(input_dir, test_images[0])
    print(f"🧪 Testando com: {test_images[0]}")
    
    # Pipeline
    print("📸 Topografo...")
    dados_visuais = topografo.analisar(test_img)
    
    print("📝 Editor...")
    texto_teste = "Anéis Dourados Zircônia R$ 79,90"
    dados_texto = editor.processar(texto_teste, dados_visuais)
    
    print("🎨 Diagramador (Vogue Style)...")
    output_path = diagramador.renderizar(
        imagem_path=test_img,
        dados_texto=dados_texto,
        dados_visuais=dados_visuais,
        formato="original",
        paleta="vogue",  # ← NOVA PALETA
        modo_preco="padrao"
    )
    
    print(f"✅ Resultado salvo em: {output_path}")
else:
    print("❌ Nenhuma imagem encontrada em input/")
