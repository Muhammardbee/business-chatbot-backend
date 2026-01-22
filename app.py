# =========================
# REQUIRED IMPORTS
# =========================
from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import os

# =========================
# APP INITIALIZATION
# =========================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")  # Needed for sessions

# =========================
# DATABASE CONFIGURATION
# =========================
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGO_URI)
mongo = client[DB_NAME]  # Renamed variable for clarity

# =========================
# SETUP ADMIN USER (RUN ONCE)
# =========================
@app.route("/setup-admin")
def setup_admin():
    # Delete old admin user if exists
    mongo.users.delete_many({"username": "admin"})

    # Generate hashed password
    hashed_password = generate_password_hash("admin123")

    # Insert admin user
    mongo.users.insert_one({
        "username": "admin",
        "password": hashed_password,
        "role": "admin"
    })

    return "Admin user recreated successfully. Username: admin | Password: admin123"

# =========================
# LOGIN ROUTE
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = mongo.users.find_one({"username": username})

        # Safety checks
        if not user:
            return render_template("login.html", error="Invalid username or password")

        if "password" not in user:
            return "User exists but has no password. Please run /setup-admin again.", 500

        if not check_password_hash(user["password"], password):
            return render_template("login.html", error="Invalid username or password")

        # Login successful, store session
        session["user_id"] = str(user["_id"])
        session["username"] = user["username"]
        session["role"] = user["role"]

        return redirect("/admin/dashboard")

    return render_template("login.html")
