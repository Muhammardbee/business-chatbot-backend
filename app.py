from flask import Flask, request, render_template, redirect, url_for, session
from twilio.twiml.messaging_response import MessagingResponse
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

# =====================
# DATABASE
# =====================
MONGO_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_col = db["users"]
products_col = db["products"]
orders_col = db["orders"]

# =====================
# HELPERS
# =====================
def login_required(role=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                return "Access Denied", 403
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# =====================
# HOME
# =====================
@app.route("/")
def home():
    return "Backend is running 🚀"

# =====================
# LOGIN
# =====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = users_col.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin/dashboard")
            else:
                return redirect("/sales/dashboard")

        return "Invalid login details", 401

    return render_template("login.html")

# =====================
# LOGOUT
# =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =====================
# ADMIN DASHBOARD
# =====================
@app.route("/admin/dashboard")
@login_required(role="admin")
def admin_dashboard():
    products = list(products_col.find())
    users = list(users_col.find({}, {"password": 0}))
    return render_template("admin_dashboard.html", products=products, users=users)

# =====================
# ADD PRODUCT
# =====================
@app.route("/admin/add-product", methods=["POST"])
@login_required(role="admin")
def add_product():
    products_col.insert_one({
        "name": request.form["name"],
        "quantity": int(request.form["quantity"]),
        "price": float(request.form["price"]),
        "created_at": datetime.utcnow()
    })
    return redirect("/admin/dashboard")

# =====================
# ADD USER
# =====================
@app.route("/admin/add-user", methods=["POST"])
@login_required(role="admin")
def add_user():
    users_col.insert_one({
        "email": request.form["email"],
        "password": generate_password_hash(request.form["password"]),
        "role": request.form["role"],
        "created_at": datetime.utcnow()
    })
    return redirect("/admin/dashboard")

# =====================
# SALES DASHBOARD
# =====================
@app.route("/sales/dashboard")
@login_required(role="sales")
def sales_dashboard():
    orders = list(orders_col.find().sort("created_at", -1))
    return render_template("sales_dashboard.html", orders=orders)

# =====================
# TWILIO WHATSAPP
# =====================
@app.route("/twilio/webhook", methods=["POST"])
def twilio_webhook():
    body = request.form.get("Body", "").lower()
    sender = request.form.get("From")

    if body.startswith("order"):
        orders_col.insert_one({
            "customer": sender,
            "product": body.replace("order", "").strip(),
            "status": "pending",
            "created_at": datetime.utcnow()
        })

    resp = MessagingResponse()
    resp.message("✅ Order received. We’ll process it shortly.")
    return str(resp)

# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(debug=True)
