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
       load_dotenv() [cite: 156]


       self.mongo_uri = os.getenv("MONGO_URI") [cite: 156]
       self.db_name = os.getenv("MONGO_DBNAME") [cite: 156]


       if not self.mongo_uri or not self.db_name:
           raise ValueError("Missing MONGO_URI or MONGO_DBNAME environment variables") [cite: 156]


       self.client = None [cite: 157]
       self.db = None [cite: 157]
       self.classifications = None [cite: 157]


   def connect(self):
       """
       Establishes connection to MongoDB.
       """
       try:
           self.client = pymongo.MongoClient(self.mongo_uri) [cite: 158]
           self.db = self.client[self.db_name] [cite: 158]
           self.classifications = self.db.classifications [cite: 158]
           # Test connection
           self.client.server_info() [cite: 158]
           print("✓ Connected to MongoDB") [cite: 158]
           return True [cite: 158]
       except pymongo.errors.ConnectionFailure as error:
           print(f"✗ Failed to connect to MongoDB: {error}") [cite: 158]
           return False [cite: 158]


   # --- FIX: Changed signature to accept a dictionary to fix "Too many arguments"
   def save_classification(self, classification_data):
       """
       Save a classification result to the database.
       """
       try:
           # --- FIX: Unpack the dictionary here
           doc = {
               "image_id": classification_data["image_id"],
               "image_path": classification_data["image_path"],
               "animal_type": classification_data["animal_type"],
               "confidence": float(classification_data["confidence"]),
               "timestamp": datetime.utcnow(),
               "processing_time_ms": int(classification_data["processing_time_ms"]),
               "model_version": classification_data.get("model_version", "v1.0"),
           }


           result = self.classifications.insert_one(doc) [cite: 161]
           print(
               f"✓ Saved: {doc['image_id']} -> {doc['animal_type']} "
               f"({doc['confidence']:.2%})"
           )
           return result.inserted_id [cite: 161]


       except (pymongo.errors.PyMongoError, ValueError, TypeError, KeyError) as error:
           print(f"✗ Error saving classification: {error}") [cite: 162]
           return None [cite: 162]


   def get_recent_classifications(self, limit=10):
       """
       Retrieve recent classification results.
       """
       try:
           results = self.classifications.find().sort("timestamp", -1).limit(limit) [cite: 163]
           return list(results) [cite: 163]
       except pymongo.errors.PyMongoError as error:
           print(f"✗ Error retrieving classifications: {error}") [cite: 163]
           return [] [cite: 163]


   def get_classification_by_id(self, classification_id):
       """
       Retrieve a specific classification by its MongoDB ID.
       """
       try:
           if isinstance(classification_id, str):
               classification_id = ObjectId(classification_id) [cite: 164]
           return self.classifications.find_one({"_id": classification_id}) [cite: 164]
       except (pymongo.errors.PyMongoError, InvalidId, ValueError) as error:
           print(f"✗ Error retrieving classification: {error}") [cite: 164]
           return None [cite: 164]


   def get_classification_stats(self):
       """
       Get statistics about classifications.
       """
       try:
           total = self.classifications.count_documents({}) [cite: 166]


           # Count by animal type
           pipeline = [
               {
                   "$group": {
                       "_id": "$animal_type", [cite: 167]
                       "count": {"$sum": 1}, [cite: 167]
                       "avg_confidence": {"$avg": "$confidence"}, [cite: 167]
                   }
               },
               {"$sort": {"count": -1}}, [cite: 168]
           ]
           by_type = list(self.classifications.aggregate(pipeline)) [cite: 168]


           # Overall averages
           avg_pipeline = [
               {
                   "$group": {
                       "_id": None, [cite: 169]
                       "avg_confidence": {"$avg": "$confidence"}, [cite: 169]
                       "avg_processing_time": {"$avg": "$processing_time_ms"}, [cite: 169]
                   }
               }
           ]
           avg_result = list(self.classifications.aggregate(avg_pipeline)) [cite: 170]
           avg_confidence = avg_result[0]["avg_confidence"] if avg_result else 0 [cite: 170]
           avg_processing = avg_result[0]["avg_processing_time"] if avg_result else 0 [cite: 170]


           return {
               "total_classifications": total,
               "by_animal_type": [ [cite: 171]
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
       except pymongo.errors.PyMongoError as error: [cite: 173]
           print(f"✗ Error getting statistics: {error}") [cite: 173]
           return {
               "total_classifications": 0,
               "by_animal_type": [],
               "average_confidence": 0,
               "average_processing_time_ms": 0,
           }


   def close(self):
       """Close database connection."""
       if self.client:
           self.client.close() [cite: 174]
           print("✓ Database connection closed") [cite: 174]
