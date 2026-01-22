# =========================
# 1️⃣ IMPORTS
# =========================
from flask import Flask, request, render_template, redirect, url_for, flash, session
from twilio.twiml.messaging_response import MessagingResponse
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
messages_col = db["messages"]
orders_col = db["orders"]
products_col = db["products"]
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
            session["user_id"] = str(user["_id"])
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")


# =========================
# 5️⃣ LOGOUT ROUTE
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# 6️⃣ ADMIN DASHBOARD
# =========================
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Fetch products
    products = list(products_col.find())

    # Fetch users (only admin can see all users)
    users = list(users_col.find()) if session.get("role") == "admin" else []

    # Sales data (aggregate orders)
    orders = list(orders_col.find())
    sales_labels = [order["date"].strftime("%Y-%m-%d") for order in orders]
    sales_data = [order["total"] for order in orders]

    # Payments data
    payments = list(payments_col.find())
    payment_labels = [p["date"].strftime("%Y-%m-%d") for p in payments]
    payment_data = [p["amount"] for p in payments]

    return render_template(
        "dashboard.html",
        products=products,
        users=users,
        sales_labels=sales_labels,
        sales_data=sales_data,
        payment_labels=payment_labels,
        payment_data=payment_data,
        current_user={"username": session.get("username"), "role": session.get("role")}
    )


# =========================
# 7️⃣ ADD PRODUCT
# =========================
@app.route("/admin/add-product", methods=["POST"])
def add_product():
    if "user_id" not in session:
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
    return redirect(url_for("admin_dashboard"))


# =========================
# 8️⃣ TWILIO WHATSAPP WEBHOOK
# =========================
@app.route("/twilio/webhook", methods=["POST"])
def twilio_webhook():
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From", "").strip()

    # Save user
    users_col.update_one(
        {"whatsapp": sender},
        {"$setOnInsert": {"whatsapp": sender, "created_at": datetime.utcnow()}},
        upsert=True
    )

    # Save incoming message
    messages_col.insert_one({
        "whatsapp": sender,
        "message": incoming_msg,
        "direction": "incoming",
        "timestamp": datetime.utcnow()
    })

    # Reply
    resp = MessagingResponse()
    reply_text = (
        "👋 Hello!\n\n"
        "Your message has been received.\n"
        "You can ask for available products."
    )
    resp.message(reply_text)

    return str(resp), 200


# =========================
# 9️⃣ RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
