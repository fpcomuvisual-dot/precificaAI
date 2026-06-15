"""
Configurações centrais do PrecificaAI.
Todas as paths, constantes e env vars ficam aqui.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Paths
    BASE_DIR = Path(__file__).parent
    UPLOAD_DIR = str(BASE_DIR / "uploads")
    OUTPUT_DIR = str(BASE_DIR / "output")
    LOGOS_DIR = str(BASE_DIR / "logos")
    FONTS_DIR = str(BASE_DIR / "assets" / "fonts")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Limites
    MAX_IMAGE_SIZE_MB = 10
    MAX_IMAGE_DIMENSION = 3000      # Redimensionar se maior (lado maior)
    MAX_BATCH_SIZE = 30             # Máximo de imagens por lote
    
    # Server
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()
