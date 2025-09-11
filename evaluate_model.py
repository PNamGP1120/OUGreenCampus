import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report, confusion_matrix

# Nhãn theo TrashNet
LABELS = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

# Load model đã train
model = load_model("ml_models/waste_classifier.h5")

# Chuẩn bị generator cho test/validation
DATASET_DIR = "datasets/trashnet"

datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)

val_gen = datagen.flow_from_directory(
    DATASET_DIR,
    target_size=(224, 224),
    batch_size=32,
    subset="validation",
    shuffle=False  # ⚠️ Rất quan trọng: để y_true khớp với predict
)

# Predict
y_pred = model.predict(val_gen)
y_pred_classes = np.argmax(y_pred, axis=1)

# Ground truth
y_true = val_gen.classes

# Report
print("📊 Classification Report:")
print(classification_report(y_true, y_pred_classes, target_names=LABELS))

print("📉 Confusion Matrix:")
print(confusion_matrix(y_true, y_pred_classes))
