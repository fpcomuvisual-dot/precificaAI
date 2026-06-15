import argparse
import base64
import json
import urllib.request
from pathlib import Path

def test_api(image_path: str):
    url = "http://localhost:8005/api/tratar-imagem"
    file_path = Path(image_path)
    
    if not file_path.exists():
        print(f"Error: File not found: {image_path}")
        return

    # Read file content
    with open(file_path, "rb") as f:
        file_content = f.read()

    # Prepare multipart/form-data request
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    # Construct body
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + file_content + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    print(f"Sending request to {url} with {file_path.name}...")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            
            if result.get("success"):
                print(f"Success! {result['message']}")
                print(f"Detected boxes: {result['boxes']}")
                
                # Save output image
                img_data = base64.b64decode(result["image_base64"])
                output_path = file_path.with_name(f"cleaned_{file_path.stem}.png")
                with open(output_path, "wb") as f_out:
                    f_out.write(img_data)
                print(f"Saved cleaned image to: {output_path}")
            else:
                print("Failed:", result)
                
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", help="Path to image file")
    args = parser.parse_args()
    test_api(args.image_path)
