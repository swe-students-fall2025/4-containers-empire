"""
Unit tests for the animal classifier module.
"""

# pylint: skip-file
import os
from unittest.mock import patch, MagicMock
import numpy as np

from src.classifier import AnimalClassifier


def make_labels(tmp_path):
    """Helper to create a labels.txt file."""
    labels = tmp_path / "labels.txt"
    labels.write_text("Cat\nDog")
    return str(labels)


@patch("src.classifier.load_model")
def test_get_stats_with_db(mock_load_model, tmp_path):
    """Test that get_stats() returns DB stats when DB is connected."""
    mock_model = MagicMock()
    mock_load_model.return_value = mock_model

    labels = make_labels(tmp_path)
    clf = AnimalClassifier("/fake/model.h5", labels)

    clf.db_connected = True
    clf.db_handler = MagicMock()
    clf.db_handler.get_classification_stats.return_value = {
        "total_classifications": 10,
        "by_animal_type": [{"animal_type": "Cat", "count": 7, "avg_confidence": 0.88}],
    }

    stats = clf.get_stats()

    assert stats["total_classifications"] == 10
    assert stats["by_animal_type"][0]["animal_type"] == "Cat"


@patch("src.classifier.load_model")
def test_close_with_db(mock_load_model, tmp_path):
    """Test that close() calls the db_handler close method."""
    mock_model = MagicMock()
    mock_load_model.return_value = mock_model

    labels = make_labels(tmp_path)
    clf = AnimalClassifier("/fake/model.h5", labels)

    mock_close = MagicMock()
    clf.db_handler = MagicMock(close=mock_close)

    clf.close()
    mock_close.assert_called_once()


@patch("src.classifier.load_model")
@patch("src.classifier.load_dotenv")
def test_model_version_env(mock_env, mock_load_model, tmp_path):
    """Test model_version loads from environment variables."""
    mock_load_model.return_value = MagicMock()
    labels = tmp_path / "labels.txt"
    labels.write_text("0 Cat\n1 Dog")

    # Set env variable
    os.environ["MODEL_VERSION"] = "test-version"

    clf = AnimalClassifier(model_path="/fake/model.h5", labels_path=str(labels))
    assert clf.model_version == "test-version"


@patch("src.classifier.load_model")
@patch("src.classifier.DatabaseHandler")
def test_db_connection_failure(mock_db, mock_load_model, tmp_path):
    """Test constructor behavior when database connection fails."""
    mock_load_model.return_value = MagicMock()

    # Force DB connection failure
    mock_instance = mock_db.return_value
    mock_instance.connect.side_effect = ValueError("missing env")

    labels = tmp_path / "labels.txt"
    labels.write_text("0 Cat\n1 Dog")

    clf = AnimalClassifier(model_path="/fake/model.h5", labels_path=str(labels))
    assert clf.db_connected is False
    assert clf.db_handler is None


@patch("src.classifier.load_model")
def test_predict_ioerror(mock_load_model, tmp_path):
    """Test predict() error return when preprocess_image raises ValueError."""

    mock_model = MagicMock()

    # Force preprocess_image to raise ValueError
    with patch("src.classifier.AnimalClassifier.preprocess_image") as mock_prep:
        mock_prep.side_effect = ValueError("bad image")

        labels = tmp_path / "labels.txt"
        labels.write_text("0 Cat\n1 Dog")

        clf = AnimalClassifier(model_path="/fake/model.h5", labels_path=str(labels))

        result = clf.predict("fake.jpg")

        assert "error" in result
        assert result["error"] == "bad image"


@patch("src.classifier.load_model")
def test_get_stats_no_db(mock_load_model, tmp_path):
    """Test get_stats() returns None when DB is disabled."""
    mock_load_model.return_value = MagicMock()

    labels = tmp_path / "labels.txt"
    labels.write_text("0 Cat\n1 Dog")

    clf = AnimalClassifier(model_path="/fake/model.h5", labels_path=str(labels))
    clf.db_connected = False
    clf.db_handler = None

    assert clf.get_stats() is None


@patch("src.classifier.load_model")
def test_close_no_db(mock_load_model, tmp_path):
    """Test close() safely does nothing when db_handler is None."""
    mock_load_model.return_value = MagicMock()

    labels = tmp_path / "labels.txt"
    labels.write_text("0 Cat\n1 Dog")

    clf = AnimalClassifier(model_path="/fake/model.h5", labels_path=str(labels))
    clf.db_handler = None

    # Should not throw
    clf.close()


@patch("src.classifier.load_model")
@patch("src.classifier.DatabaseHandler")
def test_predict_saves_to_db(mock_db, mock_load_model, tmp_path):
    """
    Ensure that predict() calls save_classification() when database is connected.
    """
    # Mock model
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.3, 0.7]])
    mock_load_model.return_value = mock_model

    # Mock DB handler
    mock_db_instance = mock_db.return_value
    mock_db_instance.connect.return_value = True
    mock_db_instance.save_classification.return_value = 42

    # Create labels file
    labels = tmp_path / "labels.txt"
    labels.write_text("0 Cat\n1 Dog")

    # Create image
    img_path = tmp_path / "image.jpg"
    from PIL import Image

    Image.new("RGB", (224, 224)).save(img_path)

    clf = AnimalClassifier(model_path="/fake/model.h5", labels_path=str(labels))

    result = clf.predict(str(img_path), save_to_db=True)

    # DB should be used
    mock_db_instance.save_classification.assert_called_once()
    assert result["db_id"] == "42"


@patch("src.classifier.load_model")
@patch("src.classifier.DatabaseHandler")
def test_predict_db_enabled_but_save_returns_none(mock_db, mock_load_model, tmp_path):
    """
    Covers branch where DB handler returns None.
    """
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.9, 0.1]])
    mock_load_model.return_value = mock_model

    mock_db_instance = mock_db.return_value
    mock_db_instance.connect.return_value = True
    mock_db_instance.save_classification.return_value = None

    labels = tmp_path / "labels.txt"
    labels.write_text("0 Cat\n1 Dog")

    img_path = tmp_path / "img.jpg"
    from PIL import Image

    Image.new("RGB", (224, 224)).save(img_path)

    clf = AnimalClassifier(model_path="/fake/model.h5", labels_path=str(labels))
    result = clf.predict(str(img_path))

    assert "db_id" in result
    assert result["db_id"] is None


@patch("src.classifier.load_model")
def test_predict_all_predictions_structure(mock_load_model, tmp_path):
    """
    Covers lines building the all_predictions dictionary.
    """
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.4, 0.6]])
    mock_load_model.return_value = mock_model

    labels = tmp_path / "labels.txt"
    labels.write_text("0 Cat\n1 Dog")

    img_path = tmp_path / "image.jpg"
    from PIL import Image

    Image.new("RGB", (224, 224)).save(img_path)

    clf = AnimalClassifier(model_path="/fake/model.h5", labels_path=str(labels))

    # Disable DB to avoid branching
    clf.db_connected = False
    clf.db_handler = None

    res = clf.predict(str(img_path))

    assert res["all_predictions"] == {"0 Cat": 0.4, "1 Dog": 0.6}
    assert len(res["all_predictions"]) == 2
