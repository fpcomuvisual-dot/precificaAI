
try:
    import sys
    import os
    # Add current directory to path
    sys.path.append(os.getcwd())
    
    print("Tentando importar posicionamento_v3...")
    from agents import posicionamento_v3
    print("Import sucesso!")
    print(dir(posicionamento_v3))
except Exception as e:
    print(f"ERRO AO IMPORTAR: {e}")
    import traceback
    traceback.print_exc()
