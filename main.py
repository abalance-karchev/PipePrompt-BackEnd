from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

@app.route("/send", methods=["POST"])
def send_message():
    data = request.json
    text = data.get("text", "")
    
    if not text:
        return jsonify({"error": "Missing text"}), 400
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text})
    
    if response.status_code == 200:
        return jsonify({"status": "sent"})
    else:
        return jsonify({"error": response.text}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
