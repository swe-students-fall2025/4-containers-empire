![Lint Status](https://github.com/swe-students-fall2025/4-containers-empire/actions/workflows/lint.yml/badge.svg)

# Animal Classification System

A containerized machine learning application that classifies animals in images using a pre-trained Keras model. The system consists of three interconnected Docker containers: a machine learning worker that processes uploaded images, a Flask web application with user authentication and photo management, and a MongoDB database that stores classification results and user data.

## Features

- **Image Classification**: Uses a pre-trained Keras model to classify animals into 10 categories (Butterfly, Cat, Chicken, Cow, Dog, Elephant, Horse, Sheep, Spider, Squirrel)
- **User Authentication**: Secure login and registration system with session management
- **Photo Management**: Upload, view, and manage your animal photos with automatic classification
- **Real-time Processing**: Asynchronous worker processes photos in the background
- **Auto-refresh Interface**: Pages automatically update when classification completes
- **Classification Statistics**: Track confidence scores, processing times, and classification history

## Team Members

- [Avi Herman](https://github.com/avih7531)
- [Reece Huey](https://github.com/Coffee859)
- [Leon Lian](https://github.com/ll5373128)
- [Lanxi Lin](https://github.com/player1notfound)
- [Matthew Membreno](https://github.com/m9membreno)

## Architecture

The system consists of three main components:

1. **Machine Learning Worker** (`machine-learning-client/`): Background service that monitors the database for pending photos, classifies them using a Keras model, and updates results
2. **Web Application** (`web-app/`): Flask-based web server with user authentication, photo upload, and visualization dashboard
3. **MongoDB Database**: Stores user accounts, uploaded photos, and classification results

## Prerequisites

- Docker and Docker Compose installed
- Python 3.10+ (for local development)
- Git

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
   git clone <repository-url>
   cd 4-containers-empire
```

2. Create environment file:
```bash
   cp .env.example .env
```

3. Start all services:
```bash
   docker-compose up --build
```

4. Access the web application:
   - Open your browser to `http://localhost:5001`
   - Register a new account
   - Upload animal photos and watch them get classified automatically!

### Manual Setup (Development)

#### 1. Start MongoDB
```bash
docker run --name mongodb_container -d -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=secret \
  mongo:4.4-focal
```

#### 2. Set Up Machine Learning Worker
```bash
cd machine-learning-client

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONGO_URI="mongodb://admin:secret@localhost:27017/animal_classifier?authSource=admin"
export MONGO_DBNAME="animal_classifier"
export MODEL_PATH="models/keras_model.h5"
export LABELS_PATH="models/labels.txt"

# Run the worker
python src/worker.py
```

#### 3. Set Up Web Application
```bash
cd web-app

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONGO_URI="mongodb://admin:secret@localhost:27017/animal_classifier?authSource=admin"
export SECRET_KEY="your-secret-key-here"

# Run the Flask app
python app.py
```

Then open `http://localhost:5001` in your browser.

## Environment Variables

### Machine Learning Worker

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://admin:secret@db:27017/animal_classifier?authSource=admin` | MongoDB connection string |
| `MONGO_DBNAME` | `animal_classifier` | MongoDB database name |
| `MODEL_PATH` | `models/keras_model.h5` | Path to Keras model file |
| `LABELS_PATH` | `models/labels.txt` | Path to class labels file |
| `MODEL_VERSION` | `v1.0` | Model version identifier |

### Web Application

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://admin:secret@db:27017/animal_classifier?authSource=admin` | MongoDB connection string |
| `SECRET_KEY` | `changethiskey` | Flask session secret key (change in production!) |

### Example `.env` File

Create a `.env` file in the project root:
```env
# MongoDB Configuration
MONGO_URI=mongodb://admin:secret@db:27017/animal_classifier?authSource=admin
MONGO_DBNAME=animal_classifier

# Web App Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production

# ML Worker Configuration
MODEL_PATH=models/keras_model.h5
LABELS_PATH=models/labels.txt
MODEL_VERSION=v1.0
```

**Important:** Never commit the actual `.env` file to version control. It's already in `.gitignore`.

## MongoDB Setup

### Initial Setup

MongoDB is automatically started when using `docker-compose up`. The database uses the following configuration:

- **Port:** 27017
- **Username:** admin
- **Password:** secret
- **Database:** animal_classifier

### Database Structure

The system uses three collections:

#### `users` Collection
```json
{
  "_id": ObjectId("..."),
  "username": "john_doe",
  "email": "john@example.com",
  "password": "hashed_password"
}
```

#### `photos` Collection
```json
{
  "_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "filename": "20250119_103045_cat.jpg",
  "filepath": "/app/uploads/20250119_103045_cat.jpg",
  "animal_type": "Cat",
  "confidence": 0.9523,
  "status": "done",
  "processing_time_ms": 234,
  "model_version": "v1.0",
  "created_at": ISODate("2025-01-19T10:30:45Z"),
  "updated_at": ISODate("2025-01-19T10:30:47Z"),
  "all_predictions": {
    "Butterfly": 0.001,
    "Cat": 0.9523,
    "Dog": 0.0234,
    ...
  }
}
```

### Viewing Data

Connect to MongoDB to view stored data:
```bash
# Connect to MongoDB shell
docker exec -it mongodb_container mongo -u admin -p secret --authenticationDatabase admin

# Switch to database
use animal_classifier

# View all users
db.users.find().pretty()

# View all photos
db.photos.find().pretty()

# Find photos by status
db.photos.find({status: "done"})

# Get classification statistics
db.photos.aggregate([
   $group: { _id: "$animal_type", count: { $sum: 1 } }
])
```

### Starter Data

No starter data is required. The database will be populated automatically as:
- Users register accounts
- Users upload photos
- The ML worker processes pending photos

## Web Application Features

### User Authentication

- **Registration**: Create a new account with username, email, and password
- **Login**: Secure session-based authentication
- **Logout**: Clear session and return to login page

### Photo Management

- **Upload**: Upload animal photos (JPG, PNG formats supported)
- **View**: Browse all your uploaded photos in a grid layout
- **Details**: Click on any photo to see classification results
- **Auto-refresh**: Photo detail pages automatically refresh every 3 seconds while processing

### Classification Status

Photos can have three statuses:
- **pending**: Waiting for ML worker to process
- **done**: Classification complete with results
- **failed**: Classification encountered an error

## Project Structure
```
4-containers-empire/
├── machine-learning-client/     # ML worker subsystem
│   ├── src/
│   │   ├── worker.py           # Main worker service
│   │   ├── classifier.py       # Animal classification logic
│   │   ├── db_handler.py       # MongoDB interaction
│   │   └── __init__.py
│   ├── models/
│   │   ├── keras_model.h5      # Pre-trained Keras model
│   │   └── labels.txt          # Class labels
│   ├── tests/                  # Unit tests
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Docker configuration
├── web-app/                    # Web application subsystem
│   ├── app.py                  # Flask application
│   ├── templates/              # HTML templates
│   │   ├── home.html
│   │   ├── login.html
│   │   ├── my_animals.html
│   │   ├── upload.html
│   │   └── your_animal.html
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Docker configuration
│   └── tests/                  # Unit tests
├── uploads/                    # Shared volume for uploaded photos
├── db/                         # MongoDB data directory
├── docker-compose.yml          # Docker Compose configuration
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Development

### Code Formatting and Linting

Both subsystems use `black` for formatting and `pylint` for linting:
```bash
# Format code
black machine-learning-client/src/
black web-app/

# Lint code
cd machine-learning-client/src
pylint *.py

cd ../../web-app
pylint app.py
```

### Running Tests

#### Machine Learning Client Tests
```bash
cd machine-learning-client
pytest tests/ --cov=src --cov-report=html
```

#### Web Application Tests
```bash
cd web-app
pytest tests/ --cov=. --cov-report=html
```

### CI/CD

The project uses GitHub Actions for continuous integration:

- **Linting**: Runs `pylint` and `black --check` on every push and pull request
- Both `machine-learning-client` and `web-app` subsystems are tested

## Troubleshooting

### MongoDB Connection Issues

If containers cannot connect to MongoDB:

1. Verify MongoDB is running: `docker-compose ps`
2. Check that `mongodb_container` shows "Up" status
3. Verify connection string in environment variables
4. Ensure all containers are on the same Docker network

### Port 5001 Already in Use

If port 5001 is already in use:

1. Check what's using the port: `lsof -i :5001` (Mac/Linux)
2. On macOS, AirPlay Receiver commonly uses port 5000
   - Go to System Settings → General → AirDrop & Handoff
   - Turn off AirPlay Receiver
3. Or change the port mapping in `docker-compose.yml`:
```yaml
   ports:
     - "5002:5000"  # Map different host port
```

### Photos Stuck in "Pending" Status

If uploaded photos remain in "pending" status:

1. Check ML worker is running: `docker-compose ps`
2. View worker logs: `docker-compose logs ml-worker`
3. Verify model files exist in `machine-learning-client/models/`
4. Check file permissions on `uploads/` directory
5. Restart the worker: `docker-compose restart ml-worker`

### Images Too Large on Home Page

Images are automatically sized to 200px height with `object-fit: cover` for consistent display.

### CSS Not Loading

CSS is served via a Flask route at `/style.css`. If styles aren't applying:

1. Check browser console for 404 errors
2. Verify the route exists in `app.py`
3. Clear browser cache and hard refresh (Cmd+Shift+R or Ctrl+Shift+R)

### "User object has no attribute 'get_id'" Error

This occurs if the User class is missing the `get_id()` method required by Flask-Login. The fix is already implemented in `app.py`.

### Model Loading Errors

If the Keras model fails to load:

1. Verify `models/keras_model.h5` exists in the `machine-learning-client/` directory
2. Check that TensorFlow is installed: `pip list | grep tensorflow`
3. Ensure the model file is not corrupted
4. Check container logs: `docker-compose logs ml-worker`

## Docker Commands

### Starting Services
```bash
# Start all services
docker-compose up

# Start in detached mode (background)
docker-compose up -d

# Rebuild and start
docker-compose up --build
```

### Stopping Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes database data!)
docker-compose down -v
```

### Viewing Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web-app
docker-compose logs ml-worker
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f ml-worker
```

### Accessing Containers
```bash
# Open shell in web-app container
docker-compose exec web-app bash

# Open shell in ml-worker container
docker-compose exec ml-worker bash

# Connect to MongoDB
docker exec -it mongodb_container mongo -u admin -p secret --authenticationDatabase admin
```

## License

See [LICENSE](./LICENSE) file for details.

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Ensure code passes linting: `black --check .` and `pylint`
4. Run tests: `pytest`
5. Create a pull request
6. Get code review approval from at least one team member
7. Merge to `main`

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [MongoDB Docker](https://www.mongodb.com/compatibility/docker)
- [Docker Compose](https://docs.docker.com/compose/)