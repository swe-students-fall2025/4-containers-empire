"""
Unit tests for database handler.
"""

# pylint: skip-file
import pytest
from unittest.mock import MagicMock, patch
from src.db_handler import DatabaseHandler
import pymongo.errors


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
