from flask import Flask, request, jsonify
import requests
import os
import google.generativeai as genai

app = Flask(__name__)

# PP_KEYS = {"0000": "admin",
#            "0001": "free",
#            "0002": "free",
#            "0003": "free",
#            "0004": "free",
#            "0005": "free",
#            "0006": "free",
#            "0007": "free",
#            "0008": "free",}

TG_TOKEN = os.environ.get("TG_TOKEN").strip()
TG_CHAT_ID = os.environ.get("TG_CHAT_ID").strip()
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Logging setup (so logs show in Railway)
import logging
gunicorn_error_logger = logging.getLogger("gunicorn.error")
app.logger.handlers = gunicorn_error_logger.handlers
app.logger.setLevel(logging.INFO)

@app.post("/ask")
def ask():
    """
    Accepts: {"text": "user question"}
    Returns: {"answer": "AI response"} or sends to Telegram
    """
    if not GEMINI_API_KEY:
        return jsonify({"error": "Server not configured (missing GEMINI_API_KEY)"}), 500

    data = request.get_json(silent=True) or {}
    user_text = (data.get("text") or "").strip()
    
    if not user_text:
        return jsonify({"error": "Missing text"}), 400

    try:
        # Call Gemini
        app.logger.info("Calling Gemini with text=%s", user_text[:100])
        response = model.generate_content(user_text)
        answer = response.text
        
        # Send to Telegram
        if TG_TOKEN and TG_CHAT_ID:
            tg_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            tg_response = requests.post(
                tg_url,
                json={"chat_id": TG_CHAT_ID, "text": answer},
                timeout=10,
            )
            app.logger.info("Telegram status=%s", tg_response.status_code)
            
            if not tg_response.ok:
                app.logger.warning("Telegram error: %s", tg_response.text)
        
        return jsonify({"answer": answer, "telegram_sent": bool(TG_TOKEN and TG_CHAT_ID)}), 200
        
    except Exception as e:
        app.logger.exception("AI request failed")
        return jsonify({"error": "AI request failed", "details": str(e)}), 502

# @app.route("/register", methods=["POST"])
# def register():
#     data = request.get_json(silent=True) or {}
#     key = data.get("key")
#     if not key:
#         return jsonify({"error": "Missing key"}), 400
#     switch (PP_KEYS[key]):
#         case "admin":
#             return jsonify({"status": "admin"}), 200
#         case "free":
#             PP_KEYS[key] = data.get("device_id")
#         case _:
#             return jsonify({"error": "Invalid key"}), 400
#     return jsonify({"status": "registered"}), 200

@app.get("/health")
def health():
    return jsonify({"ok": True}), 200


@app.route("/send", methods=["POST"])
def send_message():
    if not TG_TOKEN or not TG_CHAT_ID:
        return jsonify({"error": "Server is not configured (missing TG_TOKEN or TG_CHAT_ID)"}), 500

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "Missing text"}), 400

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    app.logger.info("Telegram URL=%s", url)
    try:
        response = requests.post(
            url,
            json={"chat_id": TG_CHAT_ID, "text": text},
            timeout=10,
        )
    except requests.RequestException as e:
        app.logger.exception("Telegram request failed")
        return jsonify({"error": "Telegram request failed", "details": str(e)}), 502

    app.logger.info("Telegram status=%s body=%s", response.status_code, response.text)

    if response.ok:
        return jsonify({"status": "sent"}), 200

    return jsonify({"error": "Telegram API error", "details": response.text}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
