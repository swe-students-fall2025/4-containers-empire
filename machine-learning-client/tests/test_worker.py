"""
Unit tests for MLWorker in worker.py
"""

# pylint: skip-file
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import pytest
from bson.objectid import ObjectId


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from worker import MLWorker


@pytest.fixture
def sample_photo():
    """Provides a sample photo document with an ObjectId and fake file path."""
    return {"_id": ObjectId(), "filepath": "/fake/path.jpg", "filename": "test.jpg"}


@pytest.fixture
def mock_classifier():
    """Provides a mocked classifier object with a predictable predict() response."""
    classifier = Mock()
    classifier.predict.return_value = {
        "animal_type": "dog",
        "confidence": 0.95,
        "processing_time_ms": 123,
        "all_predictions": {"dog": 0.95},
        "model_version": "v1.0",
    }
    classifier.close = Mock()
    return classifier


@pytest.fixture
def mock_mongo_client():
    """Provides a mocked MongoDB client, database, and photos collection."""
    client = MagicMock()
    db = MagicMock()
    photos = MagicMock()
    client.__getitem__.return_value = db
    db.__getitem__.return_value = photos
    return client, db, photos


@patch("worker.pymongo.MongoClient")
@patch("worker.AnimalClassifier")
def test_init_success(mock_classifier_class, mock_mongo_client_class):
    """Test MLWorker initialization."""
    mock_classifier_class.return_value = Mock()
    mock_client_instance = MagicMock()
    mock_mongo_client_class.return_value = mock_client_instance

    with patch.dict(os.environ, {"MONGO_URI": "mongodb://fake"}):
        worker = MLWorker(poll_interval=0)
        assert worker.poll_interval == 0
        assert worker.classifier is not None
        assert worker.photos_collection is not None
        worker.close()


@patch("worker.pymongo.MongoClient")
@patch("worker.AnimalClassifier")
def test_process_photo_success(
    mock_classifier_class, mock_mongo_client_class, sample_photo
):
    """Test normal photo processing branch."""
    mock_classifier = Mock()
    mock_classifier.predict.return_value = {
        "animal_type": "cat",
        "confidence": 0.88,
        "processing_time_ms": 100,
        "all_predictions": {"cat": 0.88},
        "model_version": "v1.0",
    }
    mock_classifier.close = Mock()
    mock_classifier_class.return_value = mock_classifier

    mock_client_instance = MagicMock()
    mock_db = MagicMock()
    mock_photos = MagicMock()
    mock_photos.update_one.return_value.modified_count = 1
    mock_client_instance.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_photos
    mock_mongo_client_class.return_value = mock_client_instance

    with patch.dict(os.environ, {"MONGO_URI": "mongodb://fake"}), patch(
        "os.path.exists", return_value=True
    ):
        worker = MLWorker(poll_interval=0)
        worker._process_photo(sample_photo)
        mock_photos.update_one.assert_called()
        worker.close()


@patch("worker.pymongo.MongoClient")
@patch("worker.AnimalClassifier")
def test_process_photo_missing_filepath(mock_classifier_class, mock_mongo_client_class):
    """Test photo doc without filepath triggers failure."""
    photo = {"_id": ObjectId(), "filename": "nofile.jpg"}
    mock_classifier_class.return_value = Mock()

    mock_client_instance = MagicMock()
    mock_db = MagicMock()
    mock_photos = MagicMock()
    mock_client_instance.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_photos
    mock_mongo_client_class.return_value = mock_client_instance

    with patch.dict(os.environ, {"MONGO_URI": "mongodb://fake"}):
        worker = MLWorker(poll_interval=0)
        worker._process_photo(photo)
        # _mark_failed should call update_one
        mock_photos.update_one.assert_called()
        worker.close()


@patch("worker.pymongo.MongoClient")
@patch("worker.AnimalClassifier")
def test_process_photo_file_not_exist(
    mock_classifier_class, mock_mongo_client_class, sample_photo
):
    """Test photo processing when file does not exist."""
    mock_classifier_class.return_value = Mock()

    mock_client_instance = MagicMock()
    mock_db = MagicMock()
    mock_photos = MagicMock()
    mock_client_instance.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_photos
    mock_mongo_client_class.return_value = mock_client_instance

    with patch.dict(os.environ, {"MONGO_URI": "mongodb://fake"}), patch(
        "os.path.exists", return_value=False
    ):
        worker = MLWorker(poll_interval=0)
        worker._process_photo(sample_photo)
        mock_photos.update_one.assert_called()
        worker.close()


@patch("worker.pymongo.MongoClient")
@patch("worker.AnimalClassifier")
def test_process_photo_predict_error(
    mock_classifier_class, mock_mongo_client_class, sample_photo
):
    """Test processing when classifier.predict returns an error."""
    mock_classifier = Mock()
    mock_classifier.predict.return_value = {"error": "Failed"}
    mock_classifier_class.return_value = mock_classifier

    mock_client_instance = MagicMock()
    mock_db = MagicMock()
    mock_photos = MagicMock()
    mock_client_instance.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_photos
    mock_mongo_client_class.return_value = mock_client_instance

    with patch.dict(os.environ, {"MONGO_URI": "mongodb://fake"}), patch(
        "os.path.exists", return_value=True
    ):
        worker = MLWorker(poll_interval=0)
        worker._process_photo(sample_photo)
        mock_photos.update_one.assert_called()
        worker.close()


@patch("worker.pymongo.MongoClient")
@patch("worker.AnimalClassifier")
def test_mark_failed_exception(mock_classifier_class, mock_mongo_client_class):
    """Test _mark_failed handles update_one exception."""
    mock_classifier_class.return_value = Mock()

    mock_client_instance = MagicMock()
    mock_db = MagicMock()
    mock_photos = MagicMock()
    mock_photos.update_one.side_effect = Exception("DB fail")
    mock_client_instance.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_photos
    mock_mongo_client_class.return_value = mock_client_instance

    with patch.dict(os.environ, {"MONGO_URI": "mongodb://fake"}):
        worker = MLWorker(poll_interval=0)
        worker._mark_failed(ObjectId(), "Error")
        mock_photos.update_one.assert_called()
        worker.close()


@patch("worker.pymongo.MongoClient")
@patch("worker.AnimalClassifier")
def test_process_photo_update_not_modified(
    mock_classifier_class, mock_mongo_client_class, sample_photo
):
    """Test the branch where update_one.modified_count == 0"""
    mock_classifier = Mock()
    mock_classifier.predict.return_value = {
        "animal_type": "cat",
        "confidence": 0.88,
        "processing_time_ms": 100,
        "all_predictions": {"cat": 0.88},
        "model_version": "v1.0",
    }
    mock_classifier.close = Mock()
    mock_classifier_class.return_value = mock_classifier

    mock_client_instance = MagicMock()
    mock_db = MagicMock()
    mock_photos = MagicMock()
    mock_photos.update_one.return_value.modified_count = 0  # triggers else branch
    mock_client_instance.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_photos
    mock_mongo_client_class.return_value = mock_client_instance

    with patch.dict(os.environ, {"MONGO_URI": "mongodb://fake"}), patch(
        "os.path.exists", return_value=True
    ):
        worker = MLWorker(poll_interval=0)
        worker._process_photo(sample_photo)
        worker.close()


@patch("worker.pymongo.MongoClient")
@patch("worker.AnimalClassifier")
def test_process_photo_exception_logging(
    mock_classifier_class, mock_mongo_client_class, sample_photo
):
    """Test exception inside _process_photo triggers _mark_failed"""
    mock_classifier = Mock()
    mock_classifier.predict.side_effect = Exception("Unexpected")
    mock_classifier_class.return_value = mock_classifier

    mock_client_instance = MagicMock()
    mock_db = MagicMock()
    mock_photos = MagicMock()
    mock_client_instance.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_photos
    mock_mongo_client_class.return_value = mock_client_instance

    with patch.dict(os.environ, {"MONGO_URI": "mongodb://fake"}), patch(
        "os.path.exists", return_value=True
    ):
        worker = MLWorker(poll_interval=0)
        worker._process_photo(sample_photo)
        mock_photos.update_one.assert_called()  # ensure _mark_failed called
        worker.close()
