"""Flask web application for Who's That Animal."""

from __future__ import annotations

import datetime
import os
from typing import Optional

from bson.objectid import ObjectId
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from pymongo import MongoClient
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "changethiskey")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["whos_that_animal"]
photos_collection = db["photos"]
users_collection = db["users"]

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


class User:
    """User model wrapping MongoDB documents for Flask-Login."""

    def __init__(self, user_doc: dict):
        """Initialize a User wrapper from a MongoDB user document."""
        self.id = str(user_doc["_id"])
        self.username = user_doc.get("username", "")

    @property
    def is_authenticated(self) -> bool:
        """Return True because this simple model assumes all users are active."""
        return True

    @property
    def is_active(self) -> bool:
        """Return True indicating the user is active."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Return False because this user is not anonymous."""
        return False


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    """Load and return a User object from MongoDB using a user ID."""
    doc = users_collection.find_one({"_id": ObjectId(user_id)})
    return User(doc) if doc else None


@app.route("/")
@login_required
def home():
    """Render the homepage displaying the user's most recent uploads."""
    query = {"user_id": ObjectId(current_user.id)}
    recent = list(photos_collection.find(query).sort("created_at", -1).limit(6))
    return render_template("home.html", recent=recent)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Display login page and authenticate on POST."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = users_collection.find_one({"username": username, "password": password})
        if user:
            login_user(User(user))
            return redirect(url_for("home"))
        flash("Invalid login.")
    return render_template("login.html", register=False)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Display registration page and create a new user account on POST."""
    if request.method == "POST":
        username = request.form.get("username", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        if users_collection.find_one({"username": username}):
            flash("Oopsie poopsie! :( That name's already taken.")
        else:
            users_collection.insert_one(
                {
                    "username": username,
                    "email": email,
                    "password": password,
                }
            )
            flash("Account created! Log in to your new account.")
            return redirect(url_for("login"))
    return render_template("login.html", register=True)


@app.route("/logout")
@login_required
def logout():
    """Log the user out and return to the login page."""
    logout_user()
    return redirect(url_for("login"))


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """Render an upload form or process an uploaded file on POST."""
    if request.method == "POST":
        file = request.files.get("image")
        if not file or not file.filename:
            flash("Please upload a file.")
            return redirect(request.url)
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = secure_filename(f"{timestamp}_{file.filename}")
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
        doc = {
            "user_id": ObjectId(current_user.id),
            "filename": filename,
            "filepath": save_path,
            "species": None,
            "confidence": None,
            "status": "pending",
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
        }
        inserted = photos_collection.insert_one(doc)
        return redirect(url_for("your_animal", obs_id=str(inserted.inserted_id)))
    return render_template("upload.html")


@app.route("/my_animal/<obs_id>")
@login_required
def your_animal(obs_id: str):
    """Display details and ML classification for a specific uploaded image."""
    obs = photos_collection.find_one({"_id": ObjectId(obs_id)})
    if not obs:
        flash("Animal not found.")
        return redirect(url_for("home"))
    return render_template("your_animal.html", obs=obs)


@app.route("/my_animals")
@login_required
def my_animals():
    """Display all uploaded images belonging to the current user."""
    query = {"user_id": ObjectId(current_user.id)}
    observations = list(photos_collection.find(query).sort("created_at", -1))
    return render_template("my_animals.html", observations=observations)


@app.route("/uploads/<filename>")
def uploaded_file(filename: str):
    """Serve user-uploaded files from the uploads directory."""
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
