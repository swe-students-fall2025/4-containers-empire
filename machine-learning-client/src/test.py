"""
Test script for animal classification model.
"""

# used copilot to help me supress the pylint errors

import os
import sys

# Suppress TensorFlow warnings (must be set before importing tensorflow)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF messages
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN custom operations

# pylint: disable=wrong-import-position,import-error,no-name-in-module
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image, ImageOps
import numpy as np
# pylint: enable=wrong-import-position,import-error,no-name-in-module

tf.get_logger().setLevel('ERROR')

# Suppress scientific notation for clarity
np.set_printoptions(suppress=True)

# Load the model and labels
path = os.path.join(os.path.dirname(__file__), "../models")
model = load_model(os.path.join(path, "keras_model.h5"), compile=False)
with open(os.path.join(path, "labels.txt"), "r", encoding="utf-8") as f:
    class_names = [line.strip() for line in f.readlines()]

# Check command-line argument
if len(sys.argv) < 2:
    print("Usage: python test_model.py <image_path>")
    sys.exit(1)

image_path = sys.argv[1]

# Load and preprocess the image
image = Image.open(image_path).convert("RGB")
image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)
image_array = np.asarray(image)
normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1  # normalize to [-1, 1]
data = np.expand_dims(normalized_image_array, axis=0)

# Run prediction
prediction = model.predict(data)
index = np.argmax(prediction)
class_name = class_names[index]
confidence_score = prediction[0][index]

print(f"Class: {class_name}")
print(f"Confidence: {confidence_score:.2f}")
