from flask import Flask, request, jsonify
import requests, os, re

app = Flask(__name__)
API_KEY = os.environ.get("GEMINI_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

@app.route("/")
def home():
    return "Freight Proxy OK"

@app.route("/analyze", methods=["POST"])
def analyze():
    if not API_KEY:
        return jsonify({"error": "GEMINI_KEY not set"}), 500
    data = request.json
    pdf_b64 = data.get("pdf_b64", "")
    prompt = data.get("prompt", "")
    body = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_b64}},
                {"text": prompt}
            ]
        }],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 4000}
    }
    try:
        r = requests.post(f"{GEMINI_URL}?key={API_KEY}", json=body, timeout=90)
        if r.status_code != 200:
            return jsonify({"error": f"Gemini {r.status_code}: {r.text[:300]}"}), 500
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text).strip()
        return jsonify({"result": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
