import sys
print("Starting diagnosis...")

try:
    print("Importing numpy...")
    import numpy as np
    print("Numpy imported.")
except Exception as e:
    print(f"Numpy failed: {e}")

try:
    print("Importing torch...")
    import torch
    print(f"Torch imported: {torch.__version__}")
except Exception as e:
    print(f"Torch failed: {e}")

try:
    print("Importing cv2...")
    import cv2
    print("cv2 imported.")
except Exception as e:
    print(f"cv2 failed: {e}")

try:
    print("Importing easyocr...")
    import easyocr
    print("easyocr imported.")
except Exception as e:
    print(f"easyocr failed: {e}")

try:
    print("Importing simple_lama_inpainting...")
    from simple_lama_inpainting import SimpleLama
    print("SimpleLama imported. Initializing...")
    lama = SimpleLama()
    print("SimpleLama initialized.")
except Exception as e:
    print(f"SimpleLama failed: {e}")

print("Diagnosis complete.")
