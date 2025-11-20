"""
Animal classification module using a pre-trained Keras model.
Now includes database integration.
"""

import os
import time
from datetime import datetime

# Suppress TensorFlow warnings (must be set before importing tensorflow)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# pylint: disable=wrong-import-position,import-error,no-name-in-module
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image, ImageOps
import numpy as np
from dotenv import load_dotenv
from db_handler import DatabaseHandler

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
        # --- Additions ---
        load_dotenv()
        self.model_version = os.getenv("MODEL_VERSION", "v1.0")
        # --- End of additions ---

        if model_path is None:
            base_path = os.path.join(os.path.dirname(__file__), "../models")
            model_path = os.path.join(base_path, "keras_model.h5")
        if labels_path is None:
            base_path = os.path.join(os.path.dirname(__file__), "../models")
            labels_path = os.path.join(base_path, "labels.txt")

        self.model = load_model(model_path, compile=False)
        self.class_names = self._load_labels(labels_path)

        # inside __init__
        try:
            self.db_handler = DatabaseHandler()
            self.db_connected = self.db_handler.connect()
        except ValueError:
            # Missing env variables → disable DB integration for tests
            self.db_handler = None
            self.db_connected = False

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
        # Using original ImageOps.fit method
        image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)
        image_array = np.asarray(image)
        normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
        return np.expand_dims(normalized_image_array, axis=0)

    def predict(self, image_path, save_to_db=True):
        """
        Classify an animal in an image and optionally save to database.

        Args:
            image_path: Path to the image file
            save_to_db: Whether to save result to database

        Returns:
            Dictionary with classification results
        """
        start_time = time.time()

        try:
            #  Original preprocessing and prediction logic
            data = self.preprocess_image(image_path)
            prediction = self.model.predict(data, verbose=0)
            index = np.argmax(prediction)
            class_name = self.class_names[index]
            confidence_score = float(prediction[0][index])

            # --- Logic added ---
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Solved "Too many local variables"
            image_id = (
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
                f"{os.path.basename(image_path)}"
            )

            result = {
                "image_id": image_id,
                "image_path": image_path,
                "animal_type": class_name,  # Using variable name
                "confidence": confidence_score,  # Using variable name
                "processing_time_ms": processing_time_ms,
                "model_version": self.model_version,
                "all_predictions": {
                    self.class_names[i]: float(prediction[0][i])
                    for i in range(len(self.class_names))
                },
            }

            # Save to database if connected and requested
            if save_to_db and self.db_connected:
                # --- FIX: This line is now formatted to pass 'black' ---
                db_id = self.db_handler.save_classification(classification_data=result)
                result["db_id"] = str(db_id) if db_id else None

            return result

        except FileNotFoundError:
            raise

        except (IOError, ValueError) as error:
            print(f"✗ Error classifying image: {error}")
            # Return a structured error
            return {"image_path": image_path, "error": str(error)}

    # --- Methods added ---

    def get_stats(self):
        """Get classification statistics from database."""
        if self.db_connected:
            return self.db_handler.get_classification_stats()
        return None

    def close(self):
        """Clean up resources."""
        if self.db_handler:
            self.db_handler.close()


def main():
    """Main function for testing the classifier."""
    print("=" * 60)
    print("Animal Classifier with Database Integration")
    print("=" * 60)

    # Initialize classifier
    classifier = AnimalClassifier()  # Changed to your class name

    # Example usage
    # Uncomment and modify the path when testing
    # image_path = "path/to/your/test/image.jpg" (insert actual image path when testing)
    # result = classifier.predict(image_path) # Changed to method name
    # print(f"\nClassification: {result['animal_type']} ({result['confidence']:.2%})")

    # Get statistics
    stats = classifier.get_stats()
    if stats:
        print("\n📊 Database Statistics:")
        print(f"  Total Classifications: {stats['total_classifications']}")
        if stats["by_animal_type"]:
            print("\n  By Animal Type:")
            for item in stats["by_animal_type"]:
                print(
                    f"    {item['animal_type']}: {item['count']} "
                    f"(avg confidence: {item['avg_confidence']:.2%})"
                )

    # Clean up
    classifier.close()


if __name__ == "__main__":
    main()
