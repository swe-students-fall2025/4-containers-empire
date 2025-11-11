from pymongo import MongoClient
from datetime import datetime


class Database:
    def __init__(self, connection_string="mongodb://localhost:27017/", db_name="animal_classifier"):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db["classifications"]
    
    def save_classification(self, image_name, predicted_class, confidence):
        document = {
            "image_name": image_name,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "timestamp": datetime.now()
        }
        result = self.collection.insert_one(document)
        return result.inserted_id
    
    def get_all_classifications(self):
        return list(self.collection.find())
    
    def get_recent_classifications(self, limit=10):
        return list(self.collection.find().sort("timestamp", -1).limit(limit))
    
    def close(self):
        self.client.close()

