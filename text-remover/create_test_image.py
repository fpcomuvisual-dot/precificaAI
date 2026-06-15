from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Create image
img = Image.new('RGB', (500, 500), color='white')
d = ImageDraw.Draw(img)

# Add text
# Try to load a font, fallback to default
try:
    font = ImageFont.truetype("arial.ttf", 60)
except:
    font = ImageFont.load_default()

d.text((100, 100), "PRECO: R$ 50,00", fill='black', font=font)
d.text((100, 200), "COD: 12345", fill='red', font=font)

img.save("test_with_text.jpg")
print("Created test_with_text.jpg")
