"""
MongoDB database connection and operations for animal classification system.
"""

from datetime import datetime
from pymongo import MongoClient


class Database:
    """Simple MongoDB database handler for storing classification results."""

    def __init__(
        self,
        connection_string="mongodb://localhost:27017/",
        db_name="animal_classifier",
    ):
        """
        Initialize database connection.

        Args:
            connection_string: MongoDB connection URL
            db_name: Name of the database to use
        """
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db["classifications"]

    def save_classification(self, image_name, predicted_class, confidence):
        """
        Save a classification result to the database.

        Args:
            image_name: Name or path of the classified image
            predicted_class: Predicted animal class (fish, insect, mammal, reptile, bird)
            confidence: Confidence score of the prediction (0.0 to 1.0)

        Returns:
            ObjectId of the inserted document
        """
        document = {
            "image_name": image_name,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "timestamp": datetime.now(),
        }
        result = self.collection.insert_one(document)
        return result.inserted_id

    def get_all_classifications(self):
        """
        Get all classification results from the database.

        Returns:
            List of all classification documents
        """
        return list(self.collection.find())

    def get_recent_classifications(self, limit=10):
        """
        Get the most recent classification results.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of recent classification documents, sorted by timestamp (newest first)
        """
        return list(self.collection.find().sort("timestamp", -1).limit(limit))

    def close(self):
        """Close the database connection."""
        self.client.close()
