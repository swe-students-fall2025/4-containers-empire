# Machine Learning Client - Database Setup

## Bare Minimum Setup

### 1. Start MongoDB
```bash
docker run --name mongodb -d -p 27017:27017 mongo
```

### 2. Install Dependencies
```bash
cd machine-learning-client
pipenv install
```

### 3. Use the Database

```python
from database import Database

# Create connection
db = Database()

# Save a classification
db.save_classification(
    image_name="dog.jpg",
    predicted_class="mammal",
    confidence=0.98
)

# Get recent results
recent = db.get_recent_classifications(limit=10)

# Close connection
db.close()
```

## Database Schema

The `classifications` collection stores:
- `image_name`: Name/path of the classified image
- `predicted_class`: One of: fish, insect, mammal, reptile, bird
- `confidence`: Confidence score (0.0 to 1.0)
- `timestamp`: When the classification was made

