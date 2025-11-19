"""Flask web application for animal classification system."""
import os
import datetime

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
from bson.objectid import ObjectId


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "changethiskey")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["animal_classifier"]
photos_collection = db["photos"]
users_collection = db["users"]

UPLOAD_FOLDER = "/app/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


class User:
    """User model wrapping MongoDB documents for Flask-Login."""

    def __init__(self, user_doc: dict):
        """Initialize user from MongoDB document."""
        self.id = str(user_doc["_id"])
        self.username = user_doc.get("username", "")

    @property
    def is_authenticated(self) -> bool:
        """Return True if user is authenticated."""
        return True

    @property
    def is_active(self) -> bool:
        """Return True if user is active."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Return False as user is not anonymous."""
        return False

    def get_id(self) -> str:
        """Return the user ID as a string (required by Flask-Login)."""
        return self.id


@login_manager.user_loader
def load_user(user_id: str):
    """Load user by ID for Flask-Login."""
    doc = users_collection.find_one({"_id": ObjectId(user_id)})
    return User(doc) if doc else None


@app.route("/style.css")
def serve_css():
    """Serve the CSS stylesheet from templates directory."""
    css_path = os.path.join(app.root_path, "templates", "styles.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        response = app.make_response(css_content)
        response.headers["Content-Type"] = "text/css"
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response
    except FileNotFoundError:
        return "/* CSS file not found */", 404, {"Content-Type": "text/css"}


@app.route("/")
@login_required
def home():
    """Display home page with recent photos."""
    query = {"user_id": ObjectId(current_user.id)}
    recent = list(photos_collection.find(query).sort("created_at", -1).limit(6))

    for obs in recent:
        obs["_id"] = str(obs["_id"])

    return render_template("home.html", recent=recent)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
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
    """Handle user registration."""
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
    """Handle user logout."""
    logout_user()
    return redirect(url_for("login"))


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """Handle photo upload and classification request."""
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
            "animal_type": None,
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
    """Display single animal photo with classification results."""
    obs = photos_collection.find_one({"_id": ObjectId(obs_id)})
    if not obs:
        flash("Animal not found.")
        return redirect(url_for("home"))
    return render_template("your_animal.html", obs=obs)


@app.route("/my_animals")
@login_required
def my_animals():
    """Display all user's uploaded animal photos."""
    query = {"user_id": ObjectId(current_user.id)}
    observations = list(photos_collection.find(query).sort("created_at", -1))

    for obs in observations:
        obs["_id"] = str(obs["_id"])

    return render_template("my_animals.html", observations=observations)


@app.route("/uploads/<filename>")
def uploaded_file(filename: str):
    """Serve uploaded photo files."""
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
