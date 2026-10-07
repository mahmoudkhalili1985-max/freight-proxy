# Freight System — باربری آتیه گستر

## راه‌اندازی روی Render.com

### مرحله ۱ — آپلود روی GitHub
این فایل‌ها را به ریپو GitHub خود push کنید.

### مرحله ۲ — ساخت سرویس روی Render
1. به [render.com](https://render.com) بروید
2. New → Web Service
3. ریپو GitHub را انتخاب کنید
4. تنظیمات:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn server:app --timeout 120 --workers 1`
5. در بخش **Environment Variables** اضافه کنید:
   - `GEMINI_API_KEY` = کلید Gemini شما (از aistudio.google.com/apikey)

### مرحله ۳ — تنظیم AutoHotkey
1. فایل `ahk/anm_agent.ahk` را روی ویندوز اجرا کنید
2. آدرس Render را در باکس بالا وارد کنید (مثلاً https://freight-system.onrender.com)
3. مختصات ANM را با دکمه‌های 1 تا 5 تنظیم کنید
4. دکمه شروع را بزنید

## ساختار فایل‌ها
```
├── server.py          ← سرور اصلی Flask
├── requirements.txt   ← کتابخانه‌ها
├── Procfile           ← دستور اجرا برای Render
├── render.yaml        ← تنظیمات Render
├── templates/
│   ├── upload.html    ← صفحه آپلود PDF
│   ├── review.html    ← پنل مدیر
│   └── operator.html  ← پنل متصدی
└── ahk/
    └── anm_agent.ahk  ← اتوماسیون ANM
```
