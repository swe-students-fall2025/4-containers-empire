"""
Unit tests for database handler.
"""


from unittest.mock import MagicMock, patch
import pytest
from bson.objectid import ObjectId
# --- FIX: Moved import to top level
import pymongo.errors
from src.db_handler import DatabaseHandler




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
               "MONGO_DBNAME": "test_db", [cite: 118]
           },
       ):
           # Use MagicMock instead of Mock for dictionary access
           mock_client_instance = MagicMock() [cite: 118]
           mock_mongo_client.return_value = mock_client_instance [cite: 118]


           db_handler = DatabaseHandler() [cite: 118]
           result = db_handler.connect() [cite: 118]


           assert result is True [cite: 119]
           mock_mongo_client.assert_called_once() [cite: 119]


   @patch("src.db_handler.pymongo.MongoClient")
   @patch("src.db_handler.load_dotenv")
   def test_connect_failure(self, _mock_load_dotenv, mock_mongo_client):
       """Test failed database connection."""
       # --- FIX: Removed import from here [cite: 119]


       with patch.dict(
           "os.environ",
           {
               "MONGO_URI": "mongodb://test:test@localhost:27017",
               "MONGO_DBNAME": "test_db", [cite: 120]
           },
       ):
           # Simulate connection failure
           mock_mongo_client.side_effect = pymongo.errors.ConnectionFailure( [cite: 120]
               "Connection failed"
           )


           db_handler = DatabaseHandler() [cite: 120]
           result = db_handler.connect() [cite: 121]


           assert result is False [cite: 121]


   @patch("src.db_handler.pymongo.MongoClient")
   @patch("src.db_handler.load_dotenv")
   def test_save_classification(self, _mock_load_dotenv, mock_mongo_client):
       """Test saving a classification to database."""
       with patch.dict(
           "os.environ",
           {
               "MONGO_URI": "mongodb://test:test@localhost:27017",
               "MONGO_DBNAME": "test_db", [cite: 122]
           },
       ):
           # Mock MongoDB operations with MagicMock
           mock_client_instance = MagicMock() [cite: 122]
           mock_db = MagicMock() [cite: 122]
           mock_collection = MagicMock() [cite: 122]
           mock_result = MagicMock() [cite: 122]
           mock_result.inserted_id = "mock_id_123" [cite: 123]


           # Setup mock chain
           mock_client_instance.__getitem__.return_value = mock_db [cite: 123]
           mock_db.classifications = mock_collection [cite: 123]
           mock_collection.insert_one.return_value = mock_result [cite: 123]
           mock_mongo_client.return_value = mock_client_instance [cite: 123]


           db_handler = DatabaseHandler() [cite: 124]
           db_handler.connect() [cite: 124]


           # --- FIX: Create data dictionary to pass to new method signature
           test_data = {
               "image_id": "test_001",
               "image_path": "/path/to/image.jpg",
               "animal_type": "dog",
               "confidence": 0.95,
               "processing_time_ms": 150,
               "model_version": "v1.0",
           }
           result = db_handler.save_classification(classification_data=test_data)


           assert result == "mock_id_123" [cite: 125]
           mock_collection.insert_one.assert_called_once() [cite: 125]


           # Verify document structure
           call_args = mock_collection.insert_one.call_args [cite: 125]
           doc = call_args[0][0] [cite: 125]
           assert doc["image_id"] == "test_001" [cite: 125]
           assert doc["animal_type"] == "dog" [cite: 125]
           assert doc["confidence"] == 0.95 [cite: 126]
           assert doc["model_version"] == "v1.0" [cite: 126]


   @patch("src.db_handler.pymongo.MongoClient")
   @patch("src.db_handler.load_dotenv")
   def test_get_recent_classifications(self, _mock_load_dotenv, mock_mongo_client):
       """Test retrieving recent classifications."""
       with patch.dict(
           "os.environ",
           {
               "MONGO_URI": "mongodb://test:test@localhost:27017",
               "MONGO_DBNAME": "test_db", [cite: 127]
           },
       ):
           mock_docs = [ [cite: 127]
               {"image_id": "test_001", "animal_type": "dog"},
               {"image_id": "test_002", "animal_type": "cat"},
           ]


           mock_client_instance = MagicMock() [cite: 127]
           mock_db = MagicMock() [cite: 128]
           mock_collection = MagicMock() [cite: 128]
           mock_cursor = MagicMock() [cite: 128]
           mock_cursor.limit.return_value = mock_docs [cite: 128]


           # Setup mock chain
           mock_collection.find.return_value.sort.return_value = mock_cursor [cite: 128]
           mock_client_instance.__getitem__.return_value = mock_db [cite: 128]
           mock_db.classifications = mock_collection [cite: 129]
           mock_mongo_client.return_value = mock_client_instance [cite: 129]


           db_handler = DatabaseHandler() [cite: 129]
           db_handler.connect() [cite: 129]


           results = db_handler.get_recent_classifications(limit=2) [cite: 129]


           assert len(results) == 2 [cite: 129]
           assert results[0]["image_id"] == "test_001" [cite: 129]


   @patch("src.db_handler.load_dotenv")
   def test_init_missing_env_vars(self, _mock_load_dotenv):
       """Test initialization fails without environment variables."""
       with patch.dict("os.environ", {}, clear=True): [cite: 130]
           with pytest.raises(ValueError) as excinfo:
               DatabaseHandler() [cite: 130]
           assert "Missing MONGO_URI or MONGO_DBNAME" in str(excinfo.value) [cite: 130]


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
           mock_client_instance = MagicMock() [cite: 131]
           mock_db = MagicMock() [cite: 131]
           mock_collection = MagicMock() [cite: 131]


           # Mock count
           mock_collection.count_documents.return_value = 5 [cite: 132]


           # Mock aggregation results
           mock_collection.aggregate.side_effect = [ [cite: 132]
               [
                   {"_id": "dog", "count": 3, "avg_confidence": 0.9},
                   {"_id": "cat", "count": 2, "avg_confidence": 0.85}, [cite: 133]
               ],
               [
                   {
                       "_id": None,
                       "avg_confidence": 0.88, [cite: 134]
                       "avg_processing_time": 150,
                   }
               ],
           ]


           # Setup mock chain
           mock_client_instance.__getitem__.return_value = mock_db [cite: 135]
           mock_db.classifications = mock_collection [cite: 135]
           mock_mongo_client.return_value = mock_client_instance [cite: 135]


           db_handler = DatabaseHandler() [cite: 135]
           db_handler.connect() [cite: 135]


           stats = db_handler.get_classification_stats() [cite: 135]


           assert stats["total_classifications"] == 5 [cite: 135]
           assert len(stats["by_animal_type"]) == 2 [cite: 135]
           assert stats["average_confidence"] == 0.88 [cite: 136]
           assert stats["average_processing_time_ms"] == 150 [cite: 136]


   @patch("src.db_handler.pymongo.MongoClient")
   @patch("src.db_handler.load_dotenv")
   def test_get_classification_by_id(self, _mock_load_dotenv, mock_mongo_client):
       """Test retrieving classification by ID."""
       with patch.dict(
           "os.environ",
           {
               "MONGO_URI": "mongodb://test:test@localhost:27017",
               "MONGO_DBNAME": "test_db", [cite: 137]
           },
       ):
           # Create a valid ObjectId
           test_id = ObjectId() [cite: 137]
           mock_doc = {"_id": test_id, "animal_type": "dog"} [cite: 137]


           mock_client_instance = MagicMock() [cite: 137]
           mock_db = MagicMock() [cite: 137]
           mock_collection = MagicMock() [cite: 138]
           mock_collection.find_one.return_value = mock_doc [cite: 138]


           # Setup mock chain
           mock_client_instance.__getitem__.return_value = mock_db [cite: 138]
           mock_db.classifications = mock_collection [cite: 138]
           mock_mongo_client.return_value = mock_client_instance [cite: 138]


           db_handler = DatabaseHandler() [cite: 138]
           db_handler.connect() [cite: 138]


           # Test with ObjectId
           result = db_handler.get_classification_by_id(test_id) [cite: 139]
           assert result == mock_doc [cite: 139]
           assert result["animal_type"] == "dog" [cite: 139]


           # Test with string representation of ObjectId
           result = db_handler.get_classification_by_id(str(test_id)) [cite: 139]
           assert result == mock_doc [cite: 139]


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
           mock_client_instance = MagicMock() [cite: 141]
           mock_mongo_client.return_value = mock_client_instance [cite: 141]


           db_handler = DatabaseHandler() [cite: 141]
           db_handler.connect() [cite: 141]
           db_handler.close() [cite: 141]


           mock_client_instance.close.assert_called_once() [cite: 141]


   @patch("src.db_handler.pymongo.MongoClient")
   @patch("src.db_handler.load_dotenv")
   def test_save_classification_error(self, _mock_load_dotenv, mock_mongo_client):
       """Test save_classification handles errors gracefully."""
       # --- FIX: Removed import from here [cite: 142]


       with patch.dict(
           "os.environ",
           {
               "MONGO_URI": "mongodb://test:test@localhost:27017",
               "MONGO_DBNAME": "test_db",
           },
       ):
           mock_client_instance = MagicMock() [cite: 142]
           mock_db = MagicMock() [cite: 143]
           mock_collection = MagicMock() [cite: 143]


           # Simulate database error (use PyMongoError)
           mock_collection.insert_one.side_effect = pymongo.errors.PyMongoError( [cite: 143]
               "Database error"
           )


           mock_client_instance.__getitem__.return_value = mock_db [cite: 143]
           mock_db.classifications = mock_collection [cite: 144]
           mock_mongo_client.return_value = mock_client_instance [cite: 144]


           db_handler = DatabaseHandler() [cite: 144]
           db_handler.connect() [cite: 144]


           # --- FIX: Create data dictionary to pass to new method signature
           test_data = {
               "image_id": "test_001",
               "image_path": "/path/to/image.jpg",
               "animal_type": "dog",
               "confidence": 0.95,
               "processing_time_ms": 150,
           }
           result = db_handler.save_classification(classification_data=test_data)


           assert result is None [cite: 145]


   @patch("src.db_handler.pymongo.MongoClient")
   @patch("src.db_handler.load_dotenv")
   def test_get_classification_by_invalid_id(
       self, _mock_load_dotenv, mock_mongo_client
   ):
       """Test retrieving classification with invalid ID format."""
       with patch.dict(
           "os.environ", [cite: 146]
           {
               "MONGO_URI": "mongodb://test:test@localhost:27017", [cite: 146]
               "MONGO_DBNAME": "test_db", [cite: 146]
           },
       ):
           mock_client_instance = MagicMock() [cite: 146]
           mock_db = MagicMock() [cite: 146]
           mock_collection = MagicMock() [cite: 147]


           mock_client_instance.__getitem__.return_value = mock_db [cite: 147]
           mock_db.classifications = mock_collection [cite: 147]
           mock_mongo_client.return_value = mock_client_instance [cite: 147]


           db_handler = DatabaseHandler() [cite: 147]
           db_handler.connect() [cite: 147]


           # Test with invalid ObjectId string
           result = db_handler.get_classification_by_id("invalid_id") [cite: 148]


           # Should return None due to error handling
           assert result is None [cite: 148]
