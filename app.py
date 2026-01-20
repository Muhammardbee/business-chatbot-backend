from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend is running"

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    return "Message received", 200
