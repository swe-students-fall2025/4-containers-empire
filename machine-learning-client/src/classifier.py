"""
Animal classification module using a pre-trained Keras model.
Now includes database integration.
"""


import os
import time  # Added
from datetime import datetime  # Added


# Suppress TensorFlow warnings (must be set before importing tensorflow)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"


# pylint: disable=wrong-import-position,import-error,no-name-in-module
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image, ImageOps
import numpy as np
from dotenv import load_dotenv  # Added
from src.db_handler import DatabaseHandler  # Added


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
           base_path = os.path.join(os.path.dirname(__file__), "../models") [cite: 101]
           model_path = os.path.join(base_path, "keras_model.h5") [cite: 101]
       if labels_path is None:
           base_path = os.path.join(os.path.dirname(__file__), "../models") [cite: 101]
           labels_path = os.path.join(base_path, "labels.txt") [cite: 101]


       self.model = load_model(model_path, compile=False) [cite: 101]
       self.class_names = self._load_labels(labels_path) [cite: 101]


       # --- Additions ---
       self.db_handler = DatabaseHandler() [cite: 102]
       self.db_connected = self.db_handler.connect() [cite: 102]
       # --- End of additions ---


   def _load_labels(self, labels_path):
       """
       Load class labels from file.

       Args:
           labels_path: Path to labels file


       Returns:
           List of class names
       """
       with open(labels_path, "r", encoding="utf-8") as f:
           return [line.strip() for line in f.readlines()] [cite: 103]


   def preprocess_image(self, image_path):
       """
       Load and preprocess an image for classification.

       Args:
           image_path: Path to the image file


       Returns:
           Preprocessed image array ready for prediction
       """
       image = Image.open(image_path).convert("RGB") [cite: 104]
       # Using your original ImageOps.fit method
       image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS) [cite: 104]
       image_array = np.asarray(image) [cite: 104]
       normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1 [cite: 104, 105]
       return np.expand_dims(normalized_image_array, axis=0) [cite: 105]


   def predict(self, image_path, save_to_db=True):
       """
       Classify an animal in an image and optionally save to database.

       Args:
           image_path: Path to the image file
           save_to_db: Whether to save result to database


       Returns:
           Dictionary with classification results
       """
       start_time = time.time() [cite: 106]


       try:
           #  Original preprocessing and prediction logic
           data = self.preprocess_image(image_path) [cite: 107]
           prediction = self.model.predict(data, verbose=0) [cite: 107]
           index = np.argmax(prediction) [cite: 107]
           class_name = self.class_names[index] [cite: 107]
           confidence_score = float(prediction[0][index]) [cite: 107]


           # --- Logic added ---
           processing_time_ms = int((time.time() - start_time) * 1000) [cite: 107]


           # --- FIX: Combined 3 variables into 1 to solve "Too many local variables"
           image_id = (
               f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
               f"{os.path.basename(image_path)}"
           )


           result = {
               "image_id": image_id,
               "image_path": image_path,
               "animal_type": class_name,  # Using your variable name [cite: 109]
               "confidence": confidence_score,  # Using your variable name [cite: 109]
               "processing_time_ms": processing_time_ms,
               "model_version": self.model_version,
               "all_predictions": {
                   self.class_names[i]: float(prediction[0][i]) [cite: 110]
                   for i in range(len(self.class_names))
               },
           }


           # Save to database if connected and requested
           if save_to_db and self.db_connected:
               # --- FIX: Pass the entire result dictionary to the refactored method
               db_id = self.db_handler.save_classification(
                   classification_data=result
               )
               result["db_id"] = str(db_id) if db_id else None [cite: 112]


           return result


       # --- FIX: Caught more specific errors than "Exception"
       except (IOError, ValueError) as error:
           print(f"✗ Error classifying image: {error}") [cite: 112]
           # Return a structured error
           return {"image_path": image_path, "error": str(error)} [cite: 112]


   # --- Methods added --- [cite: 113]


   def get_stats(self):
       """Get classification statistics from database."""
       if self.db_connected:
           return self.db_handler.get_classification_stats() [cite: 113]
       return None [cite: 113]


   def close(self):
       """Clean up resources."""
       if self.db_handler:
           self.db_handler.close() [cite: 113]


def main():
   """Main function for testing the classifier."""
   print("=" * 60) [cite: 114]
   print("Animal Classifier with Database Integration") [cite: 114]
   print("=" * 60) [cite: 114]


   # Initialize classifier
   classifier = AnimalClassifier()  # Changed to your class name [cite: 114]


   # Example usage (you'll need to provide an actual image path)
   # Uncomment and modify the path when testing
   # image_path = "path/to/your/test/image.jpg"
   # result = classifier.predict(image_path) # Changed to your method name [cite: 114]
   # print(f"\nClassification: {result['animal_type']} ({result['confidence']:.2%})")


   # Get statistics
   stats = classifier.get_stats() [cite: 115]
   if stats:
       # --- FIX: Removed 'f' from f-string with no variables
       print("\n📊 Database Statistics:")
       print(f"  Total Classifications: {stats['total_classifications']}") [cite: 115]
       if stats["by_animal_type"]:
           print("\n  By Animal Type:") [cite: 115]
           for item in stats["by_animal_type"]:
               print(
                   f"    {item['animal_type']}: {item['count']} "
                   f"(avg confidence: {item['avg_confidence']:.2%})" [cite: 116]
               )


   # Clean up
   classifier.close() [cite: 116]


if __name__ == "__main__":
   main() [cite: 116]
