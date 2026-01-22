# =========================
# 1️⃣ IMPORTS
# =========================
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# =========================
# 2️⃣ APP INITIALIZATION
# =========================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

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
# 4️⃣ LOGIN ROUTE
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = users_col.find_one({"username": username})
        if user and check_password_hash(user["password"], password):
            session["user"] = {"username": username, "role": user["role"]}
            return redirect(url_for("dashboard"))
        return "Invalid credentials", 401
    return render_template("login.html")

# =========================
# 5️⃣ LOGOUT ROUTE
# =========================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# =========================
# 6️⃣ DASHBOARD ROUTE
# =========================
@app.route("/admin/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    # ----------------------
    # Fetch products
    # ----------------------
    products = list(products_col.find())

    # ----------------------
    # Fetch orders
    # ----------------------
    orders = list(orders_col.find().sort("created_at", -1).limit(10))

    # ----------------------
    # Totals
    # ----------------------
    total_products = products_col.count_documents({})
    total_orders = orders_col.count_documents({})
    total_payments = payments_col.count_documents({})

    # ----------------------
    # Chart Data
    # Sales over last 7 days
    # ----------------------
    sales_labels = []
    sales_data = []

    today = datetime.utcnow()
    for i in range(7):
        day = today.strftime("%Y-%m-%d")
        count = orders_col.count_documents({"created_at": {"$gte": datetime(today.year, today.month, today.day)}})
        sales_labels.append(day)
        sales_data.append(count)
        today = today.replace(day=today.day - 1) if today.day > 1 else today  # simple previous day

    # Stock Distribution
    stock_labels = [p["name"] for p in products]
    stock_data = [p["quantity"] for p in products]

    return render_template(
        "dashboard.html",
        products=products,
        orders=orders,
        total_products=total_products,
        total_orders=total_orders,
        total_payments=total_payments,
        sales_labels=sales_labels[::-1],
        sales_data=sales_data[::-1],
        stock_labels=stock_labels,
        stock_data=stock_data
    )

# =========================
# 7️⃣ ADD PRODUCT
# =========================
@app.route("/admin/add-product", methods=["POST"])
def add_product():
    if "user" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name")
    quantity = request.form.get("quantity")
    price = request.form.get("price")

    if not name or not quantity or not price:
        return "All fields are required", 400

    products_col.insert_one({
        "name": name,
        "quantity": int(quantity),
        "price": float(price),
        "created_at": datetime.utcnow()
    })

    return redirect(url_for("dashboard"))

# =========================
# 8️⃣ ADD USER (ADMIN ONLY)
# =========================
@app.route("/admin/add-user", methods=["POST"])
def add_user():
    if "user" not in session or session["user"]["role"] != "Admin":
        return "Unauthorized", 403

    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")

    if not username or not password or not role:
        return "All fields required", 400

    hashed_pw = generate_password_hash(password)
    users_col.insert_one({"username": username, "password": hashed_pw, "role": role})
    return redirect(url_for("dashboard"))

# =========================
# 9️⃣ RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
