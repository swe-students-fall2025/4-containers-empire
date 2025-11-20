"""
Unit tests for the animal classifier module.
"""

# pylint: skip-file
import os
import sys
from unittest.mock import Mock, patch
import numpy as np
import pytest
from PIL import Image

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

# pylint: disable=wrong-import-position,import-error
from classifier import AnimalClassifier

# pylint: enable=wrong-import-position,import-error


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image."""
    img_path = tmp_path / "test_image.jpg"
    img = Image.new("RGB", (224, 224), color=(100, 150, 200))
    img.save(str(img_path))
    return str(img_path)


@pytest.fixture
def sample_labels(tmp_path):
    """Create a sample labels file."""
    labels_path = tmp_path / "labels.txt"
    labels = ["0 Butterfly", "1 Cat", "2 Chicken", "3 Cow", "4 Dog"]
    with open(labels_path, "w", encoding="utf-8") as f:
        f.write("\n".join(labels))
    return str(labels_path)


@pytest.fixture
def mock_model():
    """Create a mock TensorFlow model."""
    model = Mock()
    model.predict.return_value = np.array([[0.1, 0.2, 0.05, 0.15, 0.5]])
    return model


class TestAnimalClassifier:
    """Test cases for the AnimalClassifier class."""

    @patch("classifier.load_model")
    def test_init_with_custom_paths(
        self, mock_load_model, mock_model, sample_labels, tmp_path
    ):  # pylint: disable=redefined-outer-name
        """Test classifier initialization with custom paths."""
        mock_model_path = str(tmp_path / "model.h5")
        mock_load_model.return_value = mock_model

        classifier = AnimalClassifier(
            model_path=mock_model_path, labels_path=sample_labels
        )

        assert classifier.model is not None
        assert len(classifier.class_names) == 5
        mock_load_model.assert_called_once_with(mock_model_path, compile=False)

    @patch("classifier.load_model")
    def test_load_labels(
        self, mock_load_model, mock_model, sample_labels
    ):  # pylint: disable=redefined-outer-name
        """Test loading labels from file."""
        mock_load_model.return_value = mock_model

        classifier = AnimalClassifier(
            model_path="/fake/model.h5", labels_path=sample_labels
        )

        assert classifier.class_names[0] == "0 Butterfly"
        assert classifier.class_names[4] == "4 Dog"
        assert len(classifier.class_names) == 5

    @patch("classifier.load_model")
    def test_preprocess_image(
        self, mock_load_model, mock_model, sample_labels, sample_image
    ):  # pylint: disable=redefined-outer-name
        """Test image preprocessing."""
        mock_load_model.return_value = mock_model

        classifier = AnimalClassifier(
            model_path="/fake/model.h5", labels_path=sample_labels
        )
        processed = classifier.preprocess_image(sample_image)

        # Check shape
        assert processed.shape == (1, 224, 224, 3)

        # Check normalization (values should be between -1 and 1)
        assert processed.min() >= -1.0
        assert processed.max() <= 1.0

        # Check data type
        assert processed.dtype == np.float32

    @patch("classifier.load_model")
    def test_predict(self, mock_load_model, mock_model, sample_labels, sample_image):
        """Test image classification prediction."""
        mock_load_model.return_value = mock_model

        classifier = AnimalClassifier(
            model_path="/fake/model.h5", labels_path=sample_labels
        )
        result = classifier.predict(sample_image)
        class_name = result["animal_type"]
        confidence = result["confidence"]

        assert class_name == "4 Dog"
        assert confidence == 0.5
        assert isinstance(confidence, float)
        mock_model.predict.assert_called_once()

    @patch("classifier.load_model")
    def test_predict_with_different_probabilities(
        self, mock_load_model, sample_labels, sample_image
    ):
        """Test prediction with different probability distributions."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.8, 0.1, 0.05, 0.03, 0.02]])
        mock_load_model.return_value = mock_model

        classifier = AnimalClassifier(
            model_path="/fake/model.h5", labels_path=sample_labels
        )
        result = classifier.predict(sample_image)
        class_name = result["animal_type"]
        confidence = result["confidence"]

        assert class_name == "0 Butterfly"
        assert abs(confidence - 0.8) < 0.001

    @patch("classifier.load_model")
    def test_predict_invalid_image_path(
        self, mock_load_model, mock_model, sample_labels
    ):  # pylint: disable=redefined-outer-name
        """Test prediction with invalid image path."""
        mock_load_model.return_value = mock_model

        classifier = AnimalClassifier(
            model_path="/fake/model.h5", labels_path=sample_labels
        )

        with pytest.raises(FileNotFoundError):
            classifier.predict("/nonexistent/image.jpg")

    @patch("classifier.load_model")
    def test_multiple_predictions(
        self, mock_load_model, mock_model, sample_labels, sample_image
    ):
        """Test making multiple predictions with the same classifier."""
        mock_load_model.return_value = mock_model

        classifier = AnimalClassifier(
            model_path="/fake/model.h5", labels_path=sample_labels
        )

        # First prediction
        result1 = classifier.predict(sample_image)
        class_name1 = result1["animal_type"]
        confidence1 = result1["confidence"]
        assert class_name1 == "4 Dog"
        assert confidence1 == 0.5

        # Second prediction
        result2 = classifier.predict(sample_image)
        class_name2 = result2["animal_type"]
        confidence2 = result2["confidence"]
        assert class_name2 == "4 Dog"
        assert confidence2 == 0.5

        # Model should be called twice
        assert mock_model.predict.call_count == 2

    @patch("classifier.load_model")
    def test_preprocess_image_size(
        self, mock_load_model, mock_model, sample_labels, tmp_path
    ):  # pylint: disable=redefined-outer-name
        """Test preprocessing images of different sizes."""
        mock_load_model.return_value = mock_model

        # Create an image with a different size
        large_img_path = tmp_path / "large_image.jpg"
        large_img = Image.new("RGB", (500, 300), color=(200, 100, 50))
        large_img.save(str(large_img_path))

        classifier = AnimalClassifier(
            model_path="/fake/model.h5", labels_path=sample_labels
        )
        processed = classifier.preprocess_image(str(large_img_path))

        # Should be resized to 224x224
        assert processed.shape == (1, 224, 224, 3)
