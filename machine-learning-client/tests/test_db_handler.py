"""
Unit tests for database handler.
"""

# pylint: skip-file
from unittest.mock import MagicMock, patch
import pytest
from bson.objectid import ObjectId
import pymongo.errors
from src.db_handler import DatabaseHandler


@patch("src.db_handler.load_dotenv")
def test_save_classification_keyerror(_mock_load_dotenv):
    """Test save_classification raises KeyError internally."""
    handler = DatabaseHandler.__new__(DatabaseHandler)
    handler.classifications = MagicMock()
    # Missing required keys
    data = {"image_path": "/x.jpg"}
    result = handler.save_classification(data)
    assert result is None


@patch("src.db_handler.load_dotenv")
def test_get_recent_classifications_error(_mock_load_dotenv):
    """Simulate PyMongoError in get_recent_classifications."""
    handler = DatabaseHandler.__new__(DatabaseHandler)
    handler.classifications = MagicMock()
    handler.classifications.find.side_effect = pymongo.errors.PyMongoError()
    result = handler.get_recent_classifications()
    assert result == []


@patch("src.db_handler.load_dotenv")
def test_get_classification_by_id_invalid(_mock_load_dotenv):
    """Simulate InvalidId during get_classification_by_id."""
    handler = DatabaseHandler.__new__(DatabaseHandler)
    handler.classifications = MagicMock()
    # Invalid ID type triggers exception
    result = handler.get_classification_by_id("invalid")
    assert result is None


@patch("src.db_handler.load_dotenv")
def test_get_classification_stats_error(_mock_load_dotenv):
    """Simulate PyMongoError during get_classification_stats."""
    handler = DatabaseHandler.__new__(DatabaseHandler)
    handler.classifications = MagicMock()
    handler.classifications.count_documents.side_effect = pymongo.errors.PyMongoError()
    stats = handler.get_classification_stats()
    assert stats["total_classifications"] == 0


@patch("src.db_handler.load_dotenv")
def test_close_calls_client_close(_mock_load_dotenv):
    """Ensure client.close() is called."""
    handler = DatabaseHandler.__new__(DatabaseHandler)
    handler.client = MagicMock()
    handler.close()
    handler.client.close.assert_called_once()


class TestDatabaseHandler:
    """Test cases for DatabaseHandler class."""

    @patch("src.db_handler.pymongo.MongoClient")
    @patch("src.db_handler.load_dotenv")
    def test_connect_success(self, _mock_load_dotenv, mock_mongo_client):
        """Test successful database connection."""
        with patch.dict(
            "os.environ",
            {
                "MONGO_URI": "mongodb://test:test@localhost:27017",
                "MONGO_DBNAME": "test_db",
            },
        ):
            # Use MagicMock instead of Mock for dictionary access
            mock_client_instance = MagicMock()
            mock_mongo_client.return_value = mock_client_instance

            db_handler = DatabaseHandler()
            result = db_handler.connect()

            assert result is True
            mock_mongo_client.assert_called_once()

    @patch("src.db_handler.pymongo.MongoClient")
    @patch("src.db_handler.load_dotenv")
    def test_connect_failure(self, _mock_load_dotenv, mock_mongo_client):
        """Test failed database connection."""
        with patch.dict(
            "os.environ",
            {
                "MONGO_URI": "mongodb://test:test@localhost:27017",
                "MONGO_DBNAME": "test_db",
            },
        ):
            # Simulate connection failure
            mock_mongo_client.side_effect = pymongo.errors.ConnectionFailure(
                "Connection failed"
            )

            db_handler = DatabaseHandler()
            result = db_handler.connect()

            assert result is False

    @patch("src.db_handler.pymongo.MongoClient")
    @patch("src.db_handler.load_dotenv")
    def test_save_classification(self, _mock_load_dotenv, mock_mongo_client):
        """Test saving a classification to database."""
        with patch.dict(
            "os.environ",
            {
                "MONGO_URI": "mongodb://test:test@localhost:27017",
                "MONGO_DBNAME": "test_db",
            },
        ):
            # Mock MongoDB operations with MagicMock
            mock_client_instance = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_result = MagicMock()
            mock_result.inserted_id = "mock_id_123"

            # Setup mock chain
            mock_client_instance.__getitem__.return_value = mock_db
            mock_db.classifications = mock_collection
            mock_collection.insert_one.return_value = mock_result
            mock_mongo_client.return_value = mock_client_instance

            db_handler = DatabaseHandler()
            db_handler.connect()

            # Create data dictionary to pass to new method signature
            test_data = {
                "image_id": "test_001",
                "image_path": "/path/to/image.jpg",
                "animal_type": "dog",
                "confidence": 0.95,
                "processing_time_ms": 150,
                "model_version": "v1.0",
            }
            result = db_handler.save_classification(classification_data=test_data)

            assert result == "mock_id_123"
            mock_collection.insert_one.assert_called_once()

            # Verify document structure
            call_args = mock_collection.insert_one.call_args
            doc = call_args[0][0]
            assert doc["image_id"] == "test_001"
            assert doc["animal_type"] == "dog"
            assert doc["confidence"] == 0.95
            assert doc["model_version"] == "v1.0"

    @patch("src.db_handler.pymongo.MongoClient")
    @patch("src.db_handler.load_dotenv")
    def test_get_recent_classifications(self, _mock_load_dotenv, mock_mongo_client):
        """Test retrieving recent classifications."""
        with patch.dict(
            "os.environ",
            {
                "MONGO_URI": "mongodb://test:test@localhost:27017",
                "MONGO_DBNAME": "test_db",
            },
        ):
            mock_docs = [
                {"image_id": "test_001", "animal_type": "dog"},
                {"image_id": "test_002", "animal_type": "cat"},
            ]

            mock_client_instance = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.limit.return_value = mock_docs

            # Setup mock chain
            mock_collection.find.return_value.sort.return_value = mock_cursor
            mock_client_instance.__getitem__.return_value = mock_db
            mock_db.classifications = mock_collection
            mock_mongo_client.return_value = mock_client_instance

            db_handler = DatabaseHandler()
            db_handler.connect()

            results = db_handler.get_recent_classifications(limit=2)

            assert len(results) == 2
            assert results[0]["image_id"] == "test_001"

    @patch("src.db_handler.load_dotenv")
    def test_init_missing_env_vars(self, _mock_load_dotenv):
        """Test initialization fails without environment variables."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError) as excinfo:
                DatabaseHandler()
            assert "Missing MONGO_URI or MONGO_DBNAME" in str(excinfo.value)

    @patch("src.db_handler.pymongo.MongoClient")
    @patch("src.db_handler.load_dotenv")
    def test_get_classification_stats(self, _mock_load_dotenv, mock_mongo_client):
        """Test getting classification statistics."""
        with patch.dict(
            "os.environ",
            {
                "MONGO_URI": "mongodb://test:test@localhost:27017",
                "MONGO_DBNAME": "test_db",
            },
        ):
            mock_client_instance = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()

            # Mock count
            mock_collection.count_documents.return_value = 5

            # Mock aggregation results
            mock_collection.aggregate.side_effect = [
                [
                    {"_id": "dog", "count": 3, "avg_confidence": 0.9},
                    {"_id": "cat", "count": 2, "avg_confidence": 0.85},
                ],
                [
                    {
                        "_id": None,
                        "avg_confidence": 0.88,
                        "avg_processing_time": 150,
                    }
                ],
            ]

            # Setup mock chain
            mock_client_instance.__getitem__.return_value = mock_db
            mock_db.classifications = mock_collection
            mock_mongo_client.return_value = mock_client_instance

            db_handler = DatabaseHandler()
            db_handler.connect()

            stats = db_handler.get_classification_stats()

            assert stats["total_classifications"] == 5
            assert len(stats["by_animal_type"]) == 2
            assert stats["average_confidence"] == 0.88
            assert stats["average_processing_time_ms"] == 150

    @patch("src.db_handler.pymongo.MongoClient")
    @patch("src.db_handler.load_dotenv")
    def test_get_classification_by_id(self, _mock_load_dotenv, mock_mongo_client):
        """Test retrieving classification by ID."""
        with patch.dict(
            "os.environ",
            {
                "MONGO_URI": "mongodb://test:test@localhost:27017",
                "MONGO_DBNAME": "test_db",
            },
        ):
            # Create a valid ObjectId
            test_id = ObjectId()
            mock_doc = {"_id": test_id, "animal_type": "dog"}

            mock_client_instance = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_collection.find_one.return_value = mock_doc

            # Setup mock chain
            mock_client_instance.__getitem__.return_value = mock_db
            mock_db.classifications = mock_collection
            mock_mongo_client.return_value = mock_client_instance

            db_handler = DatabaseHandler()
            db_handler.connect()

            # Test with ObjectId
            result = db_handler.get_classification_by_id(test_id)
            assert result == mock_doc
            assert result["animal_type"] == "dog"

            # Test with string representation of ObjectId
            result = db_handler.get_classification_by_id(str(test_id))
            assert result == mock_doc

    @patch("src.db_handler.pymongo.MongoClient")
    @patch("src.db_handler.load_dotenv")
    def test_close_connection(self, _mock_load_dotenv, mock_mongo_client):
        """Test closing database connection."""
        with patch.dict(
            "os.environ",
            {
                "MONGO_URI": "mongodb://test:test@localhost:27017",
                "MONGO_DBNAME": "test_db",
            },
        ):
            mock_client_instance = MagicMock()
            mock_mongo_client.return_value = mock_client_instance

            db_handler = DatabaseHandler()
            db_handler.connect()
            db_handler.close()

            mock_client_instance.close.assert_called_once()

    @patch("src.db_handler.pymongo.MongoClient")
    @patch("src.db_handler.load_dotenv")
    def test_save_classification_error(self, _mock_load_dotenv, mock_mongo_client):
        """Test save_classification handles errors gracefully."""
        with patch.dict(
            "os.environ",
            {
                "MONGO_URI": "mongodb://test:test@localhost:27017",
                "MONGO_DBNAME": "test_db",
            },
        ):
            mock_client_instance = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()

            # Simulate database error (use PyMongoError)
            mock_collection.insert_one.side_effect = pymongo.errors.PyMongoError(
                "Database error"
            )

            mock_client_instance.__getitem__.return_value = mock_db
            mock_db.classifications = mock_collection
            mock_mongo_client.return_value = mock_client_instance

            db_handler = DatabaseHandler()
            db_handler.connect()

            # Create data dictionary to pass to new method signature
            test_data = {
                "image_id": "test_001",
                "image_path": "/path/to/image.jpg",
                "animal_type": "dog",
                "confidence": 0.95,
                "processing_time_ms": 150,
            }
            result = db_handler.save_classification(classification_data=test_data)

            assert result is None

    @patch("src.db_handler.pymongo.MongoClient")
    @patch("src.db_handler.load_dotenv")
    def test_get_classification_by_invalid_id(
        self, _mock_load_dotenv, mock_mongo_client
    ):
        """Test retrieving classification with invalid ID format."""
        with patch.dict(
            "os.environ",
            {
                "MONGO_URI": "mongodb://test:test@localhost:27017",
                "MONGO_DBNAME": "test_db",
            },
        ):
            mock_client_instance = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()

            mock_client_instance.__getitem__.return_value = mock_db
            mock_db.classifications = mock_collection
            mock_mongo_client.return_value = mock_client_instance

            db_handler = DatabaseHandler()
            db_handler.connect()

            # Test with invalid ObjectId string
            result = db_handler.get_classification_by_id("invalid_id")

            # Should return None due to error handling
            assert result is None
