from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "changethiskey"

# set up mongodb
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["whos_that_animal"]
photos_collection = db["photos"]
users_collection = db["users"]

# upload directory
UPLOAD_FOLDER = "/app/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# set up flask login
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# define user
class User:
    def __init__(self, user_doc):
        self.id = str(user_doc["_id"])
        self.username = user_doc["username"]


    @property
    def is_authenticated(self): return True
    @property
    def is_active(self): return True
    @property
    def is_anonymous(self): return False




@login_manager.user_loader
def load_user(user_id):
    doc = users_collection.find_one({"_id": ObjectId(user_id)})
    return User(doc) if doc else None

# get routes

@app.route("/")
@login_required
def home():
    recent = list(photos_collection.find({"user_id": ObjectId(current_user.id)}).sort("created_at", -1).limit(6))
    return render_template("home.html", recent=recent)

# login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users_collection.find_one({"username": username, "password": password})
        if user:
            login_user(User(user))
            return redirect(url_for("home"))
        else:
            flash("Invalid login.")
    return render_template("login.html", register=False)

# register page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Prevent duplicate usernames
        if users_collection.find_one({"username": username}):
            flash("Oopsie poopsie! :( That name's already taken.")

        else:
            users_collection.insert_one({
                "username": username,
                "email": email,
                "password": password
            })
            flash("Account created! Log in to your new account.")
            return redirect(url_for("login"))

    return render_template("login.html", register=True)

# log out
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# upload animal images to process
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("image")
        if not file or file.filename == "":
            flash("Hey, we can't work without a file!", "danger")
            return redirect(request.url)

        filename = secure_filename(
            f"{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        )
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
            "updated_at": datetime.datetime.utcnow()
        }

        inserted = photos_collection.insert_one(doc)

        return redirect(
            url_for("your_animal", obs_id=str(inserted.inserted_id))
        )

    return render_template("upload.html")

# your_animal
# view the ML client's final guess
@app.route("/my_animal/<obs_id>")
@login_required
def your_animal(obs_id):
    obs = photos_collection.find_one({"_id": ObjectId(obs_id)})
    if not obs:
        flash("Hey, either that animal doesn't exist or I'm a bad guesser!", "danger")
        return redirect(url_for("home"))
    return render_template("your_animal.html", obs=obs)

# my_animals
# view all animal photos you've uploaded so far
@app.route("/my_animals")
@login_required
def my_animals():
    observations = list(photos_collection.find({"user_id": ObjectId(current_user.id)}).sort("created_at", -1))
    return render_template("my_animals.html", observations=observations)

# serve uploaded images
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)