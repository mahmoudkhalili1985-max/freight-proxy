from flask import Flask, request, jsonify, render_template, send_from_directory
import os, json, base64, re, requests
from datetime import datetime

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "freight-2025")

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# ── صفحات ────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/review")
def review():
    return render_template("review.html")

@app.route("/operator")
def operator():
    return render_template("operator.html")

# ── تست اتصال ────────────────────────────────────────────────────
@app.route("/api/ping")
def ping():
    return jsonify({"status": "ok", "server": "render"})

# ── تحلیل PDF ────────────────────────────────────────────────────
@app.route("/api/analyze", methods=["POST"])
def analyze():
    if not GEMINI_KEY:
        return jsonify({"error": "GEMINI_API_KEY روی سرور تنظیم نشده"}), 500
    if "pdf" not in request.files:
        return jsonify({"error": "فایل PDF ارسال نشده"}), 400

    mill = request.form.get("mill", "arfeh")
    pdf_bytes = request.files["pdf"].read()

    # حجم فایل بیش از 20MB نباشد
    if len(pdf_bytes) > 20 * 1024 * 1024:
        return jsonify({"error": "حجم فایل بیش از 20 مگابایت است"}), 400

    pdf_b64 = base64.b64encode(pdf_bytes).decode()

    PROMPT_ARFEH = """این فایل PDF گزارش مشاهده حواله‌های اعلام بار از کارخانه فولاد ارفع است.
فقط بخش‌هایی که باربری «باربری آتیه گستر» دارند را استخراج کن.
بخش‌های «حمل با مشتری» را کاملاً نادیده بگیر.
فقط JSON خالص برگردان بدون توضیح یا markdown:

{
  "date": "تاریخ گزارش",
  "source": "فولاد ارفع",
  "mill": "arfeh",
  "destinations": [
    {
      "customer": "نام مشتری",
      "address": "آدرس کامل محل تخلیه",
      "orders": [
        {
          "order_number": "شماره سفارش 05150...",
          "waybill_from": "اولین شماره حواله",
          "waybill_to": "آخرین شماره حواله",
          "count": 10,
          "weight_kg": 25000,
          "grade": "گرید",
          "notes": ""
        }
      ]
    }
  ]
}

قوانین: اگر یک مشتری چند شماره سفارش دارد هر کدام جداگانه در orders.
اگر وزن‌های مختلف در یک سفارش هست جداگانه. وزن به کیلوگرم (25تن=25000)."""

    PROMPT_CHADORMALOO = """این فایل PDF گزارش لیست محصول جهت باربری از مجتمع صنعتی چادرملو است.
فقط JSON خالص برگردان بدون توضیح یا markdown:

{
  "date": "تاریخ تهیه",
  "source": "چادرملو",
  "mill": "chadormaloo",
  "destinations": [
    {
      "customer": "نام شرکت مقصد",
      "orders": [
        {
          "delivery_order": "شماره دستور تحویل کامل مثلا 404760",
          "delivery_order_short": "4 رقم آخر مثلا 4760",
          "permit_from": "اولین سریال مجوز ورود",
          "permit_to": "آخرین سریال مجوز ورود",
          "count": 5,
          "capacity": "ظرفیت مثلا 29 تن یا 27 تن",
          "tonnage_restricted": false,
          "grade": "گرید",
          "billet_size": "150*150",
          "length": "12 متری",
          "notes": ""
        }
      ]
    }
  ]
}

tonnage_restricted: اگر 25 یا 27 تن باشد true، اگر 29 تن باشد false.
اگر یک مقصد چند دستور تحویل دارد هر کدام جداگانه در orders.
اگر ابعاد شمش مختلف (130 و 150) در یک دستور هست جداگانه."""

    prompt = PROMPT_ARFEH if mill == "arfeh" else PROMPT_CHADORMALOO

    body = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": "application/pdf", "data": pdf_b64}},
            {"text": prompt}
        ]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 4000}
    }

    for attempt in range(3):
        try:
            r = requests.post(
                f"{GEMINI_URL}?key={GEMINI_KEY}",
                json=body, timeout=90
            )
            if r.status_code != 200:
                return jsonify({"error": f"Gemini {r.status_code}: {r.text[:300]}"}), 500

            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            text = re.sub(r"```json\s*", "", text)
            text = re.sub(r"```\s*", "", text).strip()
            data = json.loads(text)

            # اضافه کردن فیلدهای کمکی
            for d_idx, dest in enumerate(data.get("destinations", [])):
                for o_idx, order in enumerate(dest.get("orders", [])):
                    order["id"] = f"d{d_idx}_o{o_idx}"
                    order.setdefault("manager_approved", False)
                    order.setdefault("print_done", False)
                    order.setdefault("notes", "")
                    if mill == "chadormaloo":
                        cap = order.get("capacity", "")
                        order["needs_manager_decision"] = "29" in str(cap)
                        order["final_capacity"] = "" if order["needs_manager_decision"] else cap

            return jsonify({"status": "ok", "data": data})

        except requests.exceptions.Timeout:
            if attempt == 2:
                return jsonify({"error": "سرور Gemini پاسخ نداد — دوباره تلاش کنید"}), 500
        except json.JSONDecodeError as e:
            return jsonify({"error": f"خطا در پردازش پاسخ: {str(e)}"}), 500
        except Exception as e:
            if attempt == 2:
                return jsonify({"error": str(e)}), 500
        import time; time.sleep(2)

# ── ذخیره و صف چاپ ───────────────────────────────────────────────
print_jobs = []  # در حافظه نگه می‌داریم (Render ephemeral)

@app.route("/api/save", methods=["POST"])
def save():
    return jsonify({"status": "saved"})

@app.route("/api/send-to-print", methods=["POST"])
def send_to_print():
    global print_jobs
    print_jobs = request.json.get("jobs", [])
    return jsonify({"status": "queued", "count": len(print_jobs)})

@app.route("/api/print-queue")
def print_queue():
    global print_jobs
    if print_jobs:
        jobs = print_jobs.copy()
        print_jobs = []
        return jsonify({"status": "pending", "jobs": jobs})
    return jsonify({"status": "empty"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
