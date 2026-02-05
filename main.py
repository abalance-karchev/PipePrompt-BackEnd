from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

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
