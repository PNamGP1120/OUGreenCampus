import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report, confusion_matrix

LABELS = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

def evaluate_model():
    """
    Đánh giá model waste_classifier.h5 trên tập validation
    Trả về classification report + confusion matrix
    """
    model = load_model("ml_models/waste_classifier.h5")

    datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)

    val_gen = datagen.flow_from_directory(
        "datasets/trashnet",
        target_size=(224, 224),
        batch_size=32,
        subset="validation",
        shuffle=False
    )

    y_pred = model.predict(val_gen)
    y_pred_classes = np.argmax(y_pred, axis=1)
    y_true = val_gen.classes

    report = classification_report(
        y_true, y_pred_classes, target_names=LABELS, output_dict=True
    )
    matrix = confusion_matrix(y_true, y_pred_classes).tolist()

    return {
        "report": report,               # dict chứa precision/recall/f1
        "confusion_matrix": matrix,     # confusion matrix
        "labels": LABELS,               # class labels
    }
