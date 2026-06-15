import sys
import traceback
import numpy as np
import cv2
from PIL import Image
from services.ocr_service import detect_text
from services.mask_service import create_mask

def debug():
    try:
        print("Loading test image...")
        # Create a dummy image if file doesn't exist, or use a real path
        # Let's create a synthetic image with a white rectangle text area
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        img[:] = (200, 0, 200) # Purple background
        
        # White sticker
        cv2.rectangle(img, (50, 50), (250, 150), (255, 255, 255), -1)
        
        # Text on sticker (black)
        cv2.putText(img, "R$ 50,00", (60, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Save for reference
        cv2.imwrite("debug_input.png", img)
        print("Created debug_input.png")
        
        print("Running OCR...")
        boxes = detect_text(img)
        print(f"OCR found {len(boxes)} boxes: {boxes}")
        
        if not boxes:
            print("WARNING: OCR found no text. Creating fake box for mask test.")
            boxes = [[60, 80, 150, 40]] # Approximate text area
            
        print("Running Mask Service...")
        mask = create_mask(img, boxes)
        print("Mask created successfully.")
        
        cv2.imwrite("debug_mask.png", mask)
        print("Saved debug_mask.png")
        
    except Exception:
        print("CRITICAL ERROR CAUGHT:")
        traceback.print_exc()

if __name__ == "__main__":
    debug()
