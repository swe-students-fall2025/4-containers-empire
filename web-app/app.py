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

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.secret_key = app.config.get("SECRET_KEY", "tempsecretkey")
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    mongo_dbname = os.environ.get("MONGO_DBNAME", "whos_that_animal")
    client = pymongo.MongoClient(mongo_uri)
    db = client[mongo_dbname]

    try:
        client.admin.command("ping")
        print("Connected to MongoDB")
    except Exception as e:
        print("MongoDB Failed to Connect")

    users_collection = db.users
    photos_collection = db.photos

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    class User:
        def __init__(self, doc):
            self.doc = doc

        def get_id(self):
            return str(self.doc["_id"])

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

    @app.route("/")
    @login_required
    def home():
        user_id = str(current_user.get_id())
        recent = list(
            photos_collection.find({"user_id": user_id})
            .sort("uploaded_at", -1)
            .limit(5)
        )
        return render_template("home.html", recent=recent, current_user=current_user)

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
                filename = file.filename
                data = file.read()
                photos_collection.insert_one(
                    {
                        "user_id": str(current_user.get_id()),
                        "filename": filename,
                        "data": data,
                        "uploaded_at": datetime.utcnow(),
                        "species": None,
                        "status": "pending",
                    }
                )
                flash("Image uploaded successfully")
                return redirect(url_for("home"))
        return render_template("upload.html")

    @app.route("/my_animals")
    @login_required
    def my_animals():
        user_id = str(current_user.get_id())
        observations = list(
            photos_collection.find({"user_id": user_id}).sort("uploaded_at", -1)
        )
        return render_template("my_animals.html", observations=observations)

    @app.route("/image/<img_id>")
    @login_required
    def get_image(img_id):
        try:
            img_doc = photos_collection.find_one({"_id": ObjectId(img_id)})
            if not img_doc:
                abort(404)
            return send_file(
                io.BytesIO(img_doc["data"]),
                attachment_filename=img_doc["filename"],
                mimetype="image/jpeg",
            )
        except Exception:
            abort(404)

    return app

app = create_app()
if __name__ == "__main__":
    FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=FLASK_PORT)
