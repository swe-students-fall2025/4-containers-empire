![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)

# Containerized App Exercise

Build a containerized app that uses machine learning. See [instructions](./instructions.md) for details.

## Database Setup

This project uses MongoDB 4.0 running in a Docker container.

### Prerequisites

- Docker Desktop installed and running
- Docker Compose installed (included with Docker Desktop)

### Starting the Database

The database is automatically started when you run the entire application with Docker Compose:
```bash
# Start all services (including database)
docker-compose up -d
```

To start only the database container:
```bash
# Start only the database service
docker-compose up -d db
```

### Environment Variables Setup

The database requires environment variables for connection. Follow these steps:

1. **Copy the example environment file:**
```bash
   cp .env.example .env
```

2. **Edit `.env` with your credentials:**
```bash
   nano .env
```
   
   For local development, use these values (matching docker-compose.yml):
```
   MONGO_DBNAME=animal_classifier
   MONGO_HOST=db
   MONGO_PORT=27017
   MONGO_USERNAME=admin
   MONGO_PASSWORD=secret
   MONGO_URI=mongodb://admin:secret@db:27017/animal_classifier
```

3. **Never commit the `.env` file** - it contains sensitive credentials and is already in `.gitignore`

### Database Configuration

The MongoDB container is configured in `docker-compose.yml` with:
- **Image:** `mongo:4.0-xenial`
- **Port:** 27017 (mapped to host)
- **Authentication:** Username/password (set via environment variables)
- **Data Persistence:** Data is stored in `./db` directory on the host machine

### Verifying Database is Running

Check that the database container is running:
```bash
docker-compose ps
```

You should see `mongodb_container` with status "Up".

View database logs:
```bash
docker logs mongodb_container
```

Look for the message: `waiting for connections on port 27017`

### Accessing the Database

#### Using MongoDB Shell (from within container):
```bash
docker exec -it mongodb_container mongo -u admin -p secret
```

Once connected, you can:
```javascript
// Switch to the animal_classifier database
use animal_classifier

// Show all collections
show collections

// Query documents
db.classifications.find().pretty()
```

#### Using MongoDB Compass (GUI client):

1. Download MongoDB Compass from https://www.mongodb.com/products/compass
2. Connection string: `mongodb://admin:secret@localhost:27017`
3. Connect and explore the `animal_classifier` database

### Database Schema

The application uses the following collections:

#### `classifications` Collection

Stores animal classification results from the ML client:
```javascript
{
  "_id": ObjectId("..."),              // Auto-generated MongoDB ID
  "image_id": "img_20250115_103045",   // Unique image identifier
  "image_path": "/data/images/...",    // Path to image file
  "animal_type": "dog",                // Classified animal type
  "confidence": 0.95,                  // Model confidence (0-1)
  "timestamp": ISODate("..."),         // When classification occurred
  "processing_time_ms": 234,           // Time taken to classify (ms)
  "model_version": "v1.0"              // ML model version used
}
```

### Populating Starter Data (Optional)

To test the application with sample data:

1. **Access MongoDB shell:**
```bash
   docker exec -it mongodb_container mongo -u admin -p secret
```

2. **Create the database and collection:**
```javascript
   use animal_classifier
   db.createCollection("classifications")
```

3. **Insert sample classifications:**
```javascript
   db.classifications.insertMany([
     {
       image_id: "sample_001",
       image_path: "/data/images/sample_001.jpg",
       animal_type: "dog",
       confidence: 0.95,
       timestamp: new Date(),
       processing_time_ms: 150,
       model_version: "v1.0"
     },
     {
       image_id: "sample_002",
       image_path: "/data/images/sample_002.jpg",
       animal_type: "cat",
       confidence: 0.88,
       timestamp: new Date(),
       processing_time_ms: 145,
       model_version: "v1.0"
     },
     {
       image_id: "sample_003",
       image_path: "/data/images/sample_003.jpg",
       animal_type: "bird",
       confidence: 0.92,
       timestamp: new Date(),
       processing_time_ms: 160,
       model_version: "v1.0"
     }
   ])
```

4. **Verify data was inserted:**
```javascript
   db.classifications.count()
   // Should return: 3
   
   db.classifications.find().pretty()
```

5. **Exit the shell:**
```javascript
   exit
```

### Connecting from Python Code

Both the ML client and web app connect to MongoDB using `pymongo`:
```python
from dotenv import load_dotenv
import os
import pymongo

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = pymongo.MongoClient(os.getenv('MONGO_URI'))
db = client[os.getenv('MONGO_DBNAME')]

# Access collections
classifications = db.classifications

# Example: Insert a document
result = classifications.insert_one({
    "image_id": "img_001",
    "animal_type": "dog",
    "confidence": 0.95
})

# Example: Query documents
for doc in classifications.find():
    print(doc)
```

### Stopping the Database

To stop the database container:
```bash
# Stop all services
docker-compose down

# Data persists in ./db directory and will be available when restarted
```

To stop and remove all data:
```bash
# WARNING: This deletes all database data
docker-compose down -v
rm -rf ./db
```