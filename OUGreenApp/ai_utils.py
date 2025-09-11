import numpy as np
from tensorflow.keras.models import load_model
from PIL import Image
from io import BytesIO

# Các nhãn theo TrashNet
LABELS = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

# Load model khi server start
MODEL = load_model("ml_models/waste_classifier.h5")

def predict_waste(img_file):
    """
    img_file: InMemoryUploadedFile từ Django
    Trả về: (label, confidence)
    """
    # Đọc ảnh từ memory → Pillow
    img = Image.open(BytesIO(img_file.read())).convert("RGB")
    img = img.resize((224, 224))

    arr = np.array(img) / 255.0
    arr = np.expand_dims(arr, axis=0)

    preds = MODEL.predict(arr)[0]
    label_id = np.argmax(preds)
    confidence = float(preds[label_id])
    return LABELS[label_id], confidence
