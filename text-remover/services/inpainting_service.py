import torch
# Monkeypatch torch.jit.load to force CPU since we are on CPU-only environment
# and the model might be saved with CUDA affinity
_original_load = torch.jit.load

def _cpu_load(*args, **kwargs):
    kwargs['map_location'] = torch.device('cpu')
    return _original_load(*args, **kwargs)

torch.jit.load = _cpu_load

from simple_lama_inpainting import SimpleLama
import numpy as np
from PIL import Image

print("Initializing LaMa model (this may take a moment)...")
lama = SimpleLama()  # Checks/downloads model
print("LaMa model initialized.")

def remove_text_with_lama(image_np: np.ndarray, mask_np: np.ndarray) -> np.ndarray:
    image_pil = Image.fromarray(image_np)
    mask_pil = Image.fromarray(mask_np)
    
    result = lama(image_pil, mask_pil)  # returns PIL.Image
    return np.array(result)
