import requests
import os

url = "http://localhost:8000/api/tratar-imagem"
file_path = "input/teste_joia.jpg"

if not os.path.exists(file_path):
    # Try finding any jpg
    for f in os.listdir("input"):
        if f.lower().endswith((".jpg", ".jpeg", ".png")):
            file_path = os.path.join("input", f)
            break

print(f"Testing with file: {file_path}")

try:
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)
        
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success:", data.get("success"))
        print("Image base64 length:", len(data.get("image_base64", "")))
        print("Boxes:", data.get("boxes"))
    else:
        print("Error:", response.text)

except Exception as e:
    print(f"Exception: {e}")
