from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend is running 🚀"

@app.route("/twilio/webhook", methods=["POST"])
def twilio_webhook():
    return "Webhook received", 200

if __name__ == "__main__":
    app.run()
