"""
Animal classification module using a pre-trained Keras model.
"""

import os

# Suppress TensorFlow warnings (must be set before importing tensorflow)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# pylint: disable=wrong-import-position,import-error,no-name-in-module
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image, ImageOps
import numpy as np

# pylint: enable=wrong-import-position,import-error,no-name-in-module

tf.get_logger().setLevel("ERROR")
np.set_printoptions(suppress=True)


class AnimalClassifier:
    """Classifier for identifying animals in images."""

    def __init__(self, model_path=None, labels_path=None):
        """
        Initialize the classifier with a model and labels.

        Args:
            model_path: Path to the Keras model file
            labels_path: Path to the labels text file
        """
        if model_path is None:
            base_path = os.path.join(os.path.dirname(__file__), "../models")
            model_path = os.path.join(base_path, "keras_model.h5")
        if labels_path is None:
            base_path = os.path.join(os.path.dirname(__file__), "../models")
            labels_path = os.path.join(base_path, "labels.txt")

        self.model = load_model(model_path, compile=False)
        self.class_names = self._load_labels(labels_path)

    def _load_labels(self, labels_path):
        """
        Load class labels from file.

        Args:
            labels_path: Path to labels file

        Returns:
            List of class names
        """
        with open(labels_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]

    def preprocess_image(self, image_path):
        """
        Load and preprocess an image for classification.

        Args:
            image_path: Path to the image file

        Returns:
            Preprocessed image array ready for prediction
        """
        image = Image.open(image_path).convert("RGB")
        image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)
        image_array = np.asarray(image)
        normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
        return np.expand_dims(normalized_image_array, axis=0)

    def predict(self, image_path):
        """
        Classify an animal in an image.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (class_name, confidence_score)
        """
        data = self.preprocess_image(image_path)
        prediction = self.model.predict(data, verbose=0)
        index = np.argmax(prediction)
        class_name = self.class_names[index]
        confidence_score = float(prediction[0][index])
        return class_name, confidence_score

