"""
Database handler for storing classification results in MongoDB.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import pymongo
from bson.objectid import ObjectId
from bson.errors import InvalidId


class DatabaseHandler:
    """Handles MongoDB operations for animal classifications."""

    def __init__(self):
        """Initialize database connection."""
        load_dotenv()

        self.mongo_uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGO_DBNAME")

        if not self.mongo_uri or not self.db_name:
            raise ValueError("Missing MONGO_URI or MONGO_DBNAME environment variables")

        self.client = None
        self.db = None
        self.classifications = None

    def connect(self):
        """
        Establishes connection to MongoDB.
        """
        try:
            self.client = pymongo.MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            self.classifications = self.db.classifications
            # Test connection
            self.client.server_info()
            print("✓ Connected to MongoDB")
            return True
        except pymongo.errors.ConnectionFailure as error:
            print(f"✗ Failed to connect to MongoDB: {error}")
            return False

    def save_classification(
        self, image_id, image_path, animal_type, confidence, processing_time_ms
    ):
        """
        Save a classification result to the database.
        """
        model_version = "v1.0"
        try:
            doc = {
                "image_id": image_id,
                "image_path": image_path,
                "animal_type": animal_type,
                "confidence": float(confidence),
                "timestamp": datetime.utcnow(),
                "processing_time_ms": int(processing_time_ms),
                "model_version": model_version,
            }

            result = self.classifications.insert_one(doc)
            print(f"✓ Saved: {image_id} -> {animal_type} ({confidence:.2%})")
            return result.inserted_id

        except (pymongo.errors.PyMongoError, ValueError, TypeError) as error:
            print(f"✗ Error saving classification: {error}")
            return None

    def get_recent_classifications(self, limit=10):
        """
        Retrieve recent classification results.
        """
        try:
            results = self.classifications.find().sort("timestamp", -1).limit(limit)
            return list(results)
        except pymongo.errors.PyMongoError as error:
            print(f"✗ Error retrieving classifications: {error}")
            return []

    def get_classification_by_id(self, classification_id):
        """
        Retrieve a specific classification by its MongoDB ID.
        """
        try:
            if isinstance(classification_id, str):
                classification_id = ObjectId(classification_id)
            return self.classifications.find_one({"_id": classification_id})
        except (pymongo.errors.PyMongoError, InvalidId, ValueError) as error:
            print(f"✗ Error retrieving classification: {error}")
            return None

    def get_classification_stats(self):
        """
        Get statistics about classifications.
        """
        try:
            total = self.classifications.count_documents({})

            # Count by animal type
            pipeline = [
                {
                    "$group": {
                        "_id": "$animal_type",
                        "count": {"$sum": 1},
                        "avg_confidence": {"$avg": "$confidence"},
                    }
                },
                {"$sort": {"count": -1}},
            ]
            by_type = list(self.classifications.aggregate(pipeline))

            # Overall averages
            avg_pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "avg_confidence": {"$avg": "$confidence"},
                        "avg_processing_time": {"$avg": "$processing_time_ms"},
                    }
                }
            ]
            avg_result = list(self.classifications.aggregate(avg_pipeline))
            avg_confidence = avg_result[0]["avg_confidence"] if avg_result else 0
            avg_processing = avg_result[0]["avg_processing_time"] if avg_result else 0

            return {
                "total_classifications": total,
                "by_animal_type": [
                    {
                        "animal_type": item["_id"],
                        "count": item["count"],
                        "avg_confidence": item["avg_confidence"],
                    }
                    for item in by_type
                ],
                "average_confidence": avg_confidence,
                "average_processing_time_ms": avg_processing,
            }
        except pymongo.errors.PyMongoError as error:
            print(f"✗ Error getting statistics: {error}")
            return {
                "total_classifications": 0,
                "by_animal_type": [],
                "average_confidence": 0,
                "average_processing_time_ms": 0,
            }

    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            print("✓ Database connection closed")
