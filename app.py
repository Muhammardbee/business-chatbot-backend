# =========================
# 1️⃣ IMPORTS
# =========================
from flask import Flask, request, render_template, redirect, url_for, session, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

# =========================
# 2️⃣ APP INITIALIZATION
# =========================
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")  # For sessions

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

# =========================
# 4️⃣ HOME ROUTE
# =========================
@app.route("/")
def home():
    return redirect(url_for("login"))

# =========================
# 5️⃣ LOGIN ROUTE
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users_col.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            # Set session
            session["user_id"] = str(user["_id"])
            session["role"] = user["role"]
            session["email"] = user["email"]

            flash("Login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials", "danger")
            return render_template("login.html")

    return render_template("login.html")

# =========================
# 6️⃣ LOGOUT ROUTE
# =========================
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))

# =========================
# 7️⃣ ADMIN DASHBOARD (Role-based)
# =========================
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for("login"))

    # Only admin can see full dashboard
    if session.get("role") != "admin":
        flash("Access denied! You are not an admin.", "danger")
        return redirect(url_for("login"))

    # Fetch data
    products = list(products_col.find())
    orders = list(orders_col.find())

    return render_template("dashboard.html", products=products, orders=orders)

# =========================
# 8️⃣ ADD PRODUCT
# =========================
@app.route("/admin/add-product", methods=["POST"])
def add_product():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    name = request.form.get("name")
    quantity = request.form.get("quantity")
    price = request.form.get("price")

    if not name or not quantity or not price:
        flash("All fields are required!", "warning")
        return redirect(url_for("admin_dashboard"))

    products_col.insert_one({
        "name": name,
        "quantity": int(quantity),
        "price": float(price),
        "created_at": datetime.utcnow()
    })

    flash(f"Product '{name}' added successfully!", "success")
    return redirect(url_for("admin_dashboard"))

# =========================
# 9️⃣ USER REGISTRATION (Admin can add users)
# =========================
@app.route("/admin/add-user", methods=["POST"])
def add_user():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    if not email or not password or not role:
        flash("All fields are required!", "warning")
        return redirect(url_for("admin_dashboard"))

    # Hash password
    hashed_pw = generate_password_hash(password)

    users_col.insert_one({
        "email": email,
        "password": hashed_pw,
        "role": role,
        "created_at": datetime.utcnow()
    })

    flash(f"User '{email}' added successfully!", "success")
    return redirect(url_for("admin_dashboard"))

# =========================
#  🔟 RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
