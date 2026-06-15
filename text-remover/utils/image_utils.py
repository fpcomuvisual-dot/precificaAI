def base64_to_image(base64_str: str) -> np.ndarray:
    import base64
    from io import BytesIO
    from PIL import Image
    import numpy as np
    data = base64.b64decode(base64_str)
    return np.array(Image.open(BytesIO(data)))
