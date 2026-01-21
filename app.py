from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    return "Backend is running 🚀"

@app.route("/twilio/webhook", methods=["POST"])
def twilio_webhook():
    # Log incoming data (important for Render logs)
    print("Incoming Twilio data:", request.form)

    incoming_msg = request.form.get("Body", "")
    sender = request.form.get("From", "")

    resp = MessagingResponse()
    resp.message(f"✅ Message received: {incoming_msg}")

    return str(resp), 200

if __name__ == "__main__":
    app.run()
