"""
ML Worker Service
Continuous monitor the database for files that are pending classifications and process them using the AnimalClassifier
"""

import os
import time
import logging
from datetime import datetime
import pymongo
from bson.objecti import ObjectId
from classifier import AnimalClassifier
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


class MLWorker:
    """Worker that processes pending photo classifications."""

    def __init__(self, poll_interval=5):
        """
        Initialize the ML worker.
        """
        self.poll_interval = poll_interval

        self.mongo_uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGO_DBNAME", "animal_classifier")

        if not self.mongo_uri:
            raise ValueError("MONGO_URI environment variable is required")

        logger.info(f"Connecting to MongoDB at {self.mongo_uri}")
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.db_name]
        self.photos_collection = self.db["photos"]

        try:
            self.client.server_info()
            logger.info("✓ Connected to MongoDB")
        except pymongo.errors.ServerSelectionTimeoutError as e:
            logger.error(f"✗ MongoDB Failed to Connect: {e}")
            raise

        logger.info("Initializing ML classifier...")
        self.classifier = AnimalClassifier()
        logger.info("✓ ML classifier initialized")

    def process_pending_photos(self):
        """
        Main worker loop: continuously process pending photos.
        """
        logger.info(f"Starting worker loop (polling every {self.poll_interval}s)")

        while True:
            try:
                pending = self.photos_collection.find_one({"status": "pending"})

                if pending:
                    self._process_photo(pending)
                else:
                    logger.debug("No pending photos found")

            except KeyboardInterrupt:
                logger.info("Worker shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)

            time.sleep(self.poll_interval)

    def _process_photo(self, photo_doc):
        """
        Process a single photo document.
        """
        photo_id = photo_doc["_id"]
        filepath = photo_doc.get("filepath")
        filename = photo_doc.get("filename", "unknown")

        logger.info(f"Processing photo: {filename} (ID: {photo_id})")

        if not filepath:
            logger.error(f"Photo {photo_id} has no filepath")
            self._mark_failed(photo_id, "No filepath provided")
            return

        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            self._mark_failed(photo_id, f"File not found: {filepath}")
            return

        try:
            result = self.classifier.predict(filepath, save_to_db=False)

            if "error" in result:
                logger.error(f"Classification failed for {filename}: {result['error']}")
                self._mark_failed(photo_id, result["error"])
                return

            # Extract results
            animal_type = result.get("animal_type")
            confidence = result.get("confidence")
            processing_time_ms = result.get("processing_time_ms")

            logger.info(
                f"✓ Classified {filename} as '{animal_type}' "
                f"(confidence: {confidence:.2%}, time: {processing_time_ms}ms)"
            )

            # Update the photo document with results
            update_result = self.photos_collection.update_one(
                {"_id": photo_id},
                {
                    "$set": {
                        "animal_type": animal_type,
                        "confidence": confidence,
                        "processing_time_ms": processing_time_ms,
                        "model_version": result.get("model_version", "v1.0"),
                        "status": "done",
                        "updated_at": datetime.utcnow(),
                        "all_predictions": result.get("all_predictions", {}),
                    }
                },
            )

            if update_result.modified_count == 1:
                logger.info(f"✓ Updated photo {photo_id} with classification results")
            else:
                logger.warning(f"Photo {photo_id} was not updated (already modified?)")

        except Exception as e:
            logger.error(f"Error processing photo {photo_id}: {e}", exc_info=True)
            self._mark_failed(photo_id, str(e))

    def _mark_failed(self, photo_id, error_message):
        """
        Mark a photo as failed with error message.
        """
        try:
            self.photos_collection.update_one(
                {"_id": photo_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": error_message,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            logger.info(f"Marked photo {photo_id} as failed")
        except Exception as e:
            logger.error(f"Failed to mark photo {photo_id} as failed: {e}")

    def close(self):
        """Clean up resources."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
        if self.classifier:
            self.classifier.close()
            logger.info("Classifier closed")


def main():
    """Main entry point for the worker."""
    logger.info("=" * 60)
    logger.info("ML Worker Service Starting")
    logger.info("=" * 60)

    try:
        worker = MLWorker(poll_interval=5)
        worker.process_pending_photos()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Worker failed to start: {e}", exc_info=True)
    finally:
        if "worker" in locals():
            worker.close()

    logger.info("ML Worker Service Stopped")


if __name__ == "__main__":
    main()
