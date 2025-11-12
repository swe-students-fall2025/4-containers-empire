"""
Test script for animal classification model.
"""

import os
import sys

# Add parent directory to the path if not running as a module
sys.path.append(os.path.dirname(__file__))

# pylint: disable=wrong-import-position,import-error
from classifier import AnimalClassifier


def main(image_path):
    """
    Run classification on a single image.

    Args:
        image_path (str): Path to the image file
    """
    classifier = AnimalClassifier()
    class_name, confidence_score = classifier.predict(image_path)
    print(f"Class: {class_name}")
    print(f"Confidence: {confidence_score:.2f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test.py <image_path>")
        sys.exit(1)
    main(sys.argv[1])
