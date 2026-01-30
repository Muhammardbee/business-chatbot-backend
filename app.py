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
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# =========================
# DATABASE CONFIGURATION
# =========================
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME", "raamp_db")

client = MongoClient(MONGO_URI)
mongo = client[DB_NAME]

# =========================
# ROOT ROUTE (IMPORTANT)
# =========================
@app.route("/")
def index():
    return redirect(url_for("login"))

# =========================
# SETUP ADMIN USER (RUN ONCE, THEN DELETE)
# =========================
@app.route("/setup-admin")
def setup_admin():
    mongo.users.delete_many({"username": "admin"})

    mongo.users.insert_one({
        "username": "admin",
        "password": generate_password_hash("admin123"),
        "role": "admin"
    })

    return "Admin created → username: admin | password: admin123"

# =========================
# LOGIN ROUTE
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = mongo.users.find_one({"username": username})

        if not user or not check_password_hash(user["password"], password):
            return render_template("login.html", error="Invalid credentials")

        session["user_id"] = str(user["_id"])
        session["username"] = user["username"]
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect("/admin/dashboard")
        else:
            return redirect("/sales/dashboard")

    return render_template("login.html")

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# ADMIN DASHBOARD
# =========================
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    products = list(mongo.products.find())
    users = list(mongo.users.find())

    return render_template(
        "admin_dashboard.html",
        products=products,
        users=users
    )

# =========================
# ADD PRODUCT
# =========================
@app.route("/admin/add-product", methods=["POST"])
def add_product():
    if session.get("role") != "admin":
        return "Unauthorized", 403

    mongo.products.insert_one({
        "name": request.form["name"],
        "quantity": int(request.form["quantity"]),
        "price": float(request.form["price"])
    })

    return redirect("/admin/dashboard")

# =========================
# ADD USER
# =========================
@app.route("/admin/add-user", methods=["POST"])
def add_user():
    if session.get("role") != "admin":
        return "Unauthorized", 403

    mongo.users.insert_one({
        "username": request.form["username"],
        "password": generate_password_hash(request.form["password"]),
        "role": request.form["role"]
    })

    return redirect("/admin/dashboard")

# =========================
# SALES DASHBOARD
# =========================
@app.route("/sales/dashboard")
def sales_dashboard():
    if session.get("role") != "sales":
        return redirect(url_for("login"))

    orders = list(mongo.orders.find())
    return render_template("sales_dashboard.html", orders=orders)
