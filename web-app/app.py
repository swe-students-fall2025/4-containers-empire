import os
import io
import pymongo
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    abort,
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
from dotenv import load_dotenv
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

UPLOAD_FOLDER = "/app/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = app.config.get("SECRET_KEY", "tempsecretkey")

mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
client = pymongo.MongoClient(mongo_uri)
db = client["animal_classifier"]
users_collection = db["users"]
photos_collection = db["photos"]

try:
    client.admin.command("ping")
    print("Connected to MongoDB")
except Exception:
    print("MongoDB Failed to Connect")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User:
    def __init__(self, user_doc: dict):
        self.id = str(user_doc["_id"])
        self.username = user_doc.get("username", "")

    def get_id(self) -> str:
        return self.id

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False


@login_manager.user_loader
def load_user(user_id):
    doc = users_collection.find_one({"_id": ObjectId(user_id)})
    return User(doc) if doc else None


@app.route("/style.css")
def serve_css():
    css_path = os.path.join(app.root_path, "templates", "styles.css")
    try:
        with open(css_path, "r") as f:
            css_content = f.read()
        response = app.make_response(css_content)
        response.headers["Content-Type"] = "text/css"
        return response
    except FileNotFoundError:
        return "CSS file not found", 404


@app.route("/")
@login_required
def home():
    query = {"user_id": ObjectId(current_user.id)}
    recent = list(photos_collection.find(query).sort("created_at", -1).limit(6))
    for obs in recent:
        obs["_id"] = str(obs["_id"])
    return render_template("home.html", recent=recent)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        email = request.form.get("email")
        if users_collection.find_one({"username": username}):
            flash("username already exists")
            return redirect(url_for("register"))
        hashed = generate_password_hash(password)
        users_collection.insert_one(
            {"username": username, "hashed": hashed, "email": email}
        )
        flash("Account created successfully. Please Log in.")
        return redirect(url_for("login"))
    return render_template("login.html", register=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        user_doc = users_collection.find_one({"username": username})
        if not user_doc:
            flash("User not found")
            return redirect(url_for("login"))
        if not check_password_hash(user_doc["hashed"], password):
            flash("Incorrect password")
            return redirect(url_for("login"))
        user = User(user_doc)
        login_user(user)
        flash("Logged in successfully")
        return redirect(url_for("home"))
    return render_template("login.html", register=False)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have logged out")
    return redirect(url_for("login"))


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("image")
        if file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
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
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            inserted = photos_collection.insert_one(doc)
            return redirect(url_for("your_animal", obs_id=str(inserted.inserted_id)))
    return render_template("upload.html")


@app.route("/my_animals")
@login_required
def my_animals():
    query = {"user_id": ObjectId(current_user.id)}
    observations = list(photos_collection.find(query).sort("created_at", -1))
    for obs in observations:
        obs["_id"] = str(obs["_id"])
    return render_template("my_animals.html", observations=observations)


@app.route("/my_animal/<obs_id>")
@login_required
def your_animal(obs_id: str):
    obs = photos_collection.find_one({"_id": ObjectId(obs_id)})
    if not obs:
        flash("Animal not found.")
        return redirect(url_for("home"))
    return render_template("your_animal.html", obs=obs)


@app.route("/uploads/<filename>")
def uploaded_file(filename: str):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=FLASK_PORT)
