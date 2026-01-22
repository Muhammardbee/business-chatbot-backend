# =========================
# 1️⃣ IMPORTS
# =========================
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# =========================
# 2️⃣ APP INITIALIZATION
# =========================
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")  # for sessions

# =========================
# 3️⃣ DATABASE CONFIGURATION
# =========================
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_col = db["users"]
products_col = db["products"]
orders_col = db["orders"]
payments_col = db["payments"]

# =========================
# 4️⃣ HELPER FUNCTIONS
# =========================
def login_required(role=None):
    """Decorator to protect routes by login and role"""
    def wrapper(fn):
        from functools import wraps
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You do not have access to this page.", "danger")
                return redirect(url_for("dashboard"))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# =========================
# 5️⃣ LOGIN & LOGOUT ROUTES
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users_col.find_one({"username": username})
        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash(f"Welcome {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

# =========================
# 6️⃣ DASHBOARD ROUTE
# =========================
@app.route("/dashboard")
@login_required()
def dashboard():
    # Fetch some basic stats for charts
    total_products = products_col.count_documents({})
    total_orders = orders_col.count_documents({})
    total_payments = payments_col.count_documents({})

    # Fetch latest 10 orders
    latest_orders = list(orders_col.find().sort("created_at", -1).limit(10))

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_orders=total_orders,
        total_payments=total_payments,
        latest_orders=latest_orders,
        username=session.get("username"),
        role=session.get("role")
    )

# =========================
# 7️⃣ RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
