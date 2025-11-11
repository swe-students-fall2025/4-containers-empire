"""
Unit tests for the database module.
"""

import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

# pylint: disable=wrong-import-position,import-error
from database import Database
# pylint: enable=wrong-import-position,import-error


class TestDatabase:
    """Test cases for the Database class."""

    @patch("database.MongoClient")
    def test_init_default_connection(self, mock_mongo_client_class):
        """Test database initialization with default connection string."""
        mock_client = MagicMock()
        mock_mongo_client_class.return_value = mock_client

        db = Database()

        mock_mongo_client_class.assert_called_once_with("mongodb://localhost:27017/")
        assert db.client == mock_client

    @patch("database.MongoClient")
    def test_init_custom_connection(self, mock_mongo_client_class):
        """Test database initialization with custom connection string."""
        mock_client = MagicMock()
        mock_mongo_client_class.return_value = mock_client

        db = Database(
            connection_string="mongodb://custom:27017/",
            db_name="custom_db"
        )

        mock_mongo_client_class.assert_called_once_with("mongodb://custom:27017/")
        assert db.client == mock_client

    @patch("database.MongoClient")
    def test_save_classification(self, mock_mongo_client_class):
        """Test saving a classification result."""
        mock_client = MagicMock()
        mock_mongo_client_class.return_value = mock_client

        # Mock insert_one result
        mock_result = Mock()
        mock_result.inserted_id = "test_id_123"
        mock_client["animal_classifier"]["classifications"].insert_one.return_value = mock_result

        db = Database()
        result_id = db.save_classification("dog.jpg", "mammal", 0.95)

        # Verify insert_one was called
        mock_client["animal_classifier"]["classifications"].insert_one.assert_called_once()
        call_args = mock_client["animal_classifier"]["classifications"].insert_one.call_args[0][0]

        assert call_args["image_name"] == "dog.jpg"
        assert call_args["predicted_class"] == "mammal"
        assert call_args["confidence"] == 0.95
        assert "timestamp" in call_args
        assert isinstance(call_args["timestamp"], datetime)
        assert result_id == "test_id_123"

    @patch("database.MongoClient")
    def test_get_all_classifications(self, mock_mongo_client_class):
        """Test retrieving all classifications."""
        mock_client = MagicMock()
        mock_mongo_client_class.return_value = mock_client

        # Mock find result
        mock_data = [
            {"image_name": "cat.jpg", "predicted_class": "mammal", "confidence": 0.9},
            {"image_name": "bird.jpg", "predicted_class": "bird", "confidence": 0.85},
        ]
        mock_client["animal_classifier"]["classifications"].find.return_value = mock_data

        db = Database()
        results = db.get_all_classifications()

        mock_client["animal_classifier"]["classifications"].find.assert_called_once()
        assert len(results) == 2
        assert results[0]["image_name"] == "cat.jpg"
        assert results[1]["predicted_class"] == "bird"

    @patch("database.MongoClient")
    def test_get_recent_classifications_default_limit(self, mock_mongo_client_class):
        """Test retrieving recent classifications with default limit."""
        mock_client = MagicMock()
        mock_mongo_client_class.return_value = mock_client

        # Create a chain of mocks for find().sort().limit()
        mock_data = [
            {"image_name": "recent.jpg", "predicted_class": "bird", "confidence": 0.9}
        ]
        mock_collection = mock_client["animal_classifier"]["classifications"]
        mock_collection.find.return_value.sort.return_value.limit.return_value = mock_data

        db = Database()
        results = db.get_recent_classifications()

        mock_collection.find.assert_called_once()
        mock_collection.find.return_value.sort.assert_called_once_with("timestamp", -1)
        mock_collection.find.return_value.sort.return_value.limit.assert_called_once_with(10)
        assert len(results) == 1
        assert results[0]["image_name"] == "recent.jpg"

    @patch("database.MongoClient")
    def test_get_recent_classifications_custom_limit(self, mock_mongo_client_class):
        """Test retrieving recent classifications with custom limit."""
        mock_client = MagicMock()
        mock_mongo_client_class.return_value = mock_client

        mock_collection = mock_client["animal_classifier"]["classifications"]
        mock_collection.find.return_value.sort.return_value.limit.return_value = []

        db = Database()
        db.get_recent_classifications(limit=5)

        mock_collection.find.return_value.sort.return_value.limit.assert_called_once_with(5)

    @patch("database.MongoClient")
    def test_close_connection(self, mock_mongo_client_class):
        """Test closing database connection."""
        mock_client = MagicMock()
        mock_mongo_client_class.return_value = mock_client

        db = Database()
        db.close()

        mock_client.close.assert_called_once()

    @patch("database.MongoClient")
    def test_save_multiple_classifications(self, mock_mongo_client_class):
        """Test saving multiple classification results."""
        mock_client = MagicMock()
        mock_mongo_client_class.return_value = mock_client

        mock_result = Mock()
        mock_result.inserted_id = "test_id"
        mock_client["animal_classifier"]["classifications"].insert_one.return_value = mock_result

        db = Database()
        db.save_classification("cat.jpg", "mammal", 0.95)
        db.save_classification("bird.jpg", "bird", 0.87)
        db.save_classification("fish.jpg", "fish", 0.92)

        assert mock_client["animal_classifier"]["classifications"].insert_one.call_count == 3

    @patch("database.MongoClient")
    def test_collection_name(self, mock_mongo_client_class):
        """Test that the correct collection name is used."""
        mock_client = MagicMock()
        mock_mongo_client_class.return_value = mock_client

        db = Database()

        # Verify collection is accessed with correct name
        assert db.collection == mock_client["animal_classifier"]["classifications"]
