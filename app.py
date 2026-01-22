# =========================
# 1️⃣ IMPORTS
# =========================
from flask import Flask, request, render_template, redirect, url_for, session
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
            # Set session
            session["user_id"] = str(user["_id"])
            session["name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials", 401
    return render_template("login.html")

# =========================
# 5️⃣ LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# 6️⃣ DASHBOARD
# =========================
@app.route("/admin/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Analytics metrics
    total_sales = sum(order.get("total", 0) for order in orders_col.find())
    total_products = products_col.count_documents({})
    total_users = users_col.count_documents({})
    pending_payments = payments_col.count_documents({"status": "pending"})

    # Chart data
    # Sales chart: last 7 days
    sales_labels = []
    sales_values = []
    for order in orders_col.find().sort("created_at", -1).limit(7):
        date_label = order["created_at"].strftime("%d-%b")
        sales_labels.append(date_label)
        sales_values.append(order.get("total", 0))

    # Products chart
    product_labels = []
    product_values = []
    for p in products_col.find():
        product_labels.append(p["name"])
        product_values.append(p.get("quantity", 0))

    # Recent orders
    recent_orders = list(orders_col.find().sort("created_at", -1).limit(10))

    return render_template(
        "dashboard.html",
        total_sales=total_sales,
        total_products=total_products,
        total_users=total_users,
        pending_payments=pending_payments,
        sales_labels=sales_labels[::-1],   # reverse so oldest first
        sales_values=sales_values[::-1],
        product_labels=product_labels,
        product_values=product_values,
        orders=recent_orders
    )

# =========================
# 7️⃣ ADD PRODUCT (Admin Only)
# =========================
@app.route("/admin/add-product", methods=["POST"])
def add_product():
    if "user_id" not in session or session["role"] != "admin":
        return "Unauthorized", 403

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
# 8️⃣ RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
