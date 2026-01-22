# =========================
# 1️⃣ IMPORTS
# =========================
from flask import Flask, request, render_template, redirect, url_for
from twilio.twiml.messaging_response import MessagingResponse
from pymongo import MongoClient
import os
from datetime import datetime
from bson.objectid import ObjectId  # Needed for deleting by ID

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
# 4️⃣ HOME ROUTE
# =========================
@app.route("/", methods=["GET"])
def home():
    return "Backend is running 🚀", 200

# =========================
# 5️⃣ TWILIO WEBHOOK
# =========================
@app.route("/twilio/webhook", methods=["POST"])
def twilio_webhook():
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From", "").strip()

    users_col.update_one(
        {"whatsapp": sender},
        {"$setOnInsert": {"whatsapp": sender, "created_at": datetime.utcnow()}},
        upsert=True
    )

    messages_col.insert_one({
        "whatsapp": sender,
        "message": incoming_msg,
        "direction": "incoming",
        "timestamp": datetime.utcnow()
    })

    resp = MessagingResponse()
    reply_text = (
        "👋 Hello!\n\n"
        "Your message has been received.\n"
        "You can ask for available products."
    )
    resp.message(reply_text)

    return str(resp), 200

# =========================
# 6️⃣ ADMIN DASHBOARD
# =========================
@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    products = list(products_col.find())

    if not products:
        products = [
            {"_id": "sample1", "name": "Sample Product 1", "quantity": 10, "price": 99.99},
            {"_id": "sample2", "name": "Sample Product 2", "quantity": 5, "price": 49.99}
        ]

    return render_template("dashboard.html", products=products)

# =========================
# 7️⃣ ADD PRODUCT
# =========================
@app.route("/admin/add-product", methods=["POST"])
def add_product():
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
# 8️⃣ DELETE PRODUCT
# =========================
@app.route("/admin/delete-product/<product_id>", methods=["POST"])
def delete_product(product_id):
    # Only delete real DB items, ignore sample IDs
    if product_id.startswith("sample"):
        return redirect(url_for("admin_dashboard"))

    products_col.delete_one({"_id": ObjectId(product_id)})
    return redirect(url_for("admin_dashboard"))

# =========================
# 9️⃣ RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
