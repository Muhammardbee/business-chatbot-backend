# =========================
# 1️⃣ IMPORTS
# =========================
from flask import Flask, request, render_template, redirect, url_for
from twilio.twiml.messaging_response import MessagingResponse
from pymongo import MongoClient
import os
from datetime import datetime


# =========================
# 2️⃣ APP INITIALIZATION
# =========================
app = Flask(__name__)


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


# =========================
# 4️⃣ BASIC HOME ROUTE
# =========================
@app.route("/", methods=["GET"])
def home():
    return "Backend is running 🚀", 200


# =========================
# 5️⃣ TWILIO WHATSAPP WEBHOOK
# =========================
@app.route("/twilio/webhook", methods=["POST"])
def twilio_webhook():
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From", "").strip()

    print("Incoming message:", incoming_msg)
    print("From:", sender)

    # Save / update user
    users_col.update_one(
        {"whatsapp": sender},
        {
            "$setOnInsert": {
                "whatsapp": sender,
                "created_at": datetime.utcnow()
            }
        },
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
        "Your message has been received successfully.\n\n"
        "Soon I’ll be able to:\n"
        "• Take orders\n"
        "• Check available stock\n"
        "• Accept payments\n"
        "• Send receipts\n\n"
        "How can I help you today?"
    )

    resp.message(reply_text)

    # Save outgoing message
    messages_col.insert_one({
        "whatsapp": sender,
        "message": reply_text,
        "direction": "outgoing",
        "timestamp": datetime.utcnow()
    })

    return str(resp), 200


# =========================
# 6️⃣ ADMIN DASHBOARD
# =========================
@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    products = list(products_col.find())
    return render_template("dashboard.html", products=products)


# =========================
# 7️⃣ ADD PRODUCT ROUTE
# =========================
@app.route("/admin/add-product", methods=["POST"])
def add_product():
    name = request.form.get("name")
    quantity = request.form.get("quantity")
    price = request.form.get("price")

    if not name or not quantity or not price:
        return "All fields are required!", 400

    try:
        quantity = int(quantity)
        price = float(price)
    except ValueError:
        return "Quantity must be an integer and price must be a number.", 400

    products_col.insert_one({
        "name": name,
        "quantity": quantity,
        "price": price,
        "created_at": datetime.utcnow()
    })

    # Redirect back to dashboard
    return redirect(url_for("admin_dashboard"))


# =========================
# 8️⃣ RUN APPLICATION
# =========================
if __name__ == "__main__":
    app.run(debug=True)
