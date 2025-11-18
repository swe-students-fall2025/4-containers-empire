from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "changethiskey"

# set up mongodb
client = MongoClient("mongodb://whos-that-animal-db:27017/")
db = client["whos_that_animal"]

users_collection = db["users"]
photos_collection = db["photos"]

# set up flask login
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# define user
class User(UserMixin):
    def __init__(self, user_data):
        # user data is a document or an object id
        if isinstance(user_data, ObjectId):
            # load from database
            data = users_collection.find_one({"_id": user_data})
            if not data:
                raise ValueError("User not found in DB")
            self.id = str(data["_id"])
            self.username = data["username"]
            self.email = data["email"]
        else:
            # already a full Mongo document
            self.id = str(user_data["_id"])
            self.username = user_data["username"]
            self.email = user_data["email"]

@login_manager.user_loader
def load_user(user_id):
    # get user based on user id
    try:
        data = users_collection.find_one({"_id": ObjectId(user_id)})
        if data:
            return User(data)
    except:
        return None

    return None

# get routes

@app.route("/")
@login_required
def index():
    return render_template("home.html", username=current_user.username)

# register page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Prevent duplicate usernames
        if users_collection.find_one({"username": username}):
            return "Username already exists."

        hashed_pw = generate_password_hash(password)

        result = users_collection.insert_one({
            "username": username,
            "email": email,
            "password_hash": hashed_pw
        })

        # load the user back from DB
        saved_user = users_collection.find_one({"_id": result.inserted_id})
        user = User(saved_user)

        login_user(user)
        return redirect(url_for("home"))

    return render_template("register.html")

# login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user_data = users_collection.find_one({"username": username})

        if user_data:
            if check_password_hash(user_data["password_hash"], password):
                user = User(user_data)
                login_user(user)
                return redirect(url_for("home"))
            else:
                return "Incorrect password."

        return "User not found."

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)