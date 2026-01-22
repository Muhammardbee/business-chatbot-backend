# =========================
# 1️⃣ IMPORTS
# =========================
from flask import Flask, request, render_template, redirect, url_for, session
from twilio.twiml.messaging_response import MessagingResponse
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os


# =========================
# 2️⃣ APP INITIALIZATION
# =========================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")


# =========================
# 3️⃣ DATABASE CONFIGURATION
# =========================
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections (AUTO-created by MongoDB)
users_col = db["users"]
products_col = db["products"]
orders_col = db["orders"]
payments_col = db["payments"]
messages_col = db["messages"]


# =========================
# 4️⃣ HOME ROUTE
# =========================
@app.route("/")
def home():
    return "Backend is running 🚀"


# =========================
# 5️⃣ TEMP ADMIN SETUP (DELETE AFTER USE)
# =========================
@app.route("/setup-admin")
def setup_admin():
    email = "admin@example.com"
    password = "admin123"

    if users_col.find_one({"email": email}):
        return "Admin already exists. DELETE this route now."

    users_col.insert_one({
        "email": email,
        "password": generate_password_hash(password),
        "role": "admin",
        "created_at": datetime.utcnow()
    })

    return f"""
    ✅ Admin created<br>
    Email: {email}<br>
    Password: {password}<br><br>
    ⚠️ DELETE /setup-admin ROUTE NOW
    """


# =========================
# 6️⃣ LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users_col.find_one({"email": email})

        if not user or not check_password_hash(user["password"], password):
            return "Invalid login", 401

        session["user_id"] = str(user["_id"])
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))

        return "Login successful"

    return render_template("login.html")


# =========================
# 7️⃣ ADMIN DASHBOARD (PROTECTED)
# =========================
@app.route("/admin/dashboard")
def admin_dashboard():
    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    products = list(products_col.find())
    orders_count = orders_col.count_documents({})
    payments_total = sum(p.get("amount", 0) for p in payments_col.find())

    return render_template(
        "dashboard.html",
        products=products,
        orders_count=orders_count,
        payments_total=payments_total
    )


# =========================
# 8️⃣ ADD PRODUCT
# =========================
@app.route("/admin/add-product", methods=["POST"])
def add_product():
    if session.get("role") != "admin":
        return "Unauthorized", 403

    products_col.insert_one({
        "name": request.form["name"],
        "quantity": int(request.form["quantity"]),
        "price": float(request.form["price"]),
        "created_at": datetime.utcnow()
    })

    return redirect(url_for("admin_dashboard"))


# =========================
# 9️⃣ LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# 🔟 RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
