# YouTube Downloader Server

سيرفر لتحميل الفيديوهات من يوتيوب باستخدام yt-dlp

## النشر على Render

1. ارفع هذا المشروع إلى GitHub
2. أنشئ Web Service على Render
3. استخدم الإعدادات:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT app:app`

## API Endpoints

- `/api/health` - التحقق من صحة السيرفر
- `/api/download?url=VIDEO_URL&quality=720` - تحميل الفيديو
- `/api/analyze?url=VIDEO_URL` - تحليل الفيديو
