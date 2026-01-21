# =========================
# 1️⃣ IMPORTS
# =========================
from flask import Flask, request, render_template
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


# =========================
# 4️⃣ ROUTES
# =========================

@app.route("/", methods=["GET", "POST"])
def home():
    return "Backend is running 🚀", 200


@app.route("/twilio/webhook", methods=["POST"])
def twilio_webhook():
    # Get WhatsApp data from Twilio
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From", "").strip()

    print("Incoming message:", incoming_msg)
    print("From:", sender)

    # -------------------------
    # Save / Update User
    # -------------------------
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

    # -------------------------
    # Save Incoming Message
    # -------------------------
    messages_col.insert_one({
        "whatsapp": sender,
        "message": incoming_msg,
        "direction": "incoming",
        "timestamp": datetime.utcnow()
    })

    # -------------------------
    # Reply to User
    # -------------------------
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

    # -------------------------
    # Save Outgoing Message
    # -------------------------
    messages_col.insert_one({
        "whatsapp": sender,
        "message": reply_text,
        "direction": "outgoing",
        "timestamp": datetime.utcnow()
    })

    return str(resp), 200


# =========================
# 5️⃣ ADMIN DASHBOARD
# =========================
@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    return render_template("dashboard.html")


# =========================
# 6️⃣ RUN APP
# =========================
if __name__ == "__main__":
    app.run()
