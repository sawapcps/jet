import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ============================================
# 📥 تحميل الفيديو مع دعم الكوكيز
# ============================================
@app.route('/api/download', methods=['GET'])
def download():
    url = request.args.get('url')
    quality = request.args.get('quality', '720')
    
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    try:
        # إعدادات yt-dlp مع خيارات لتجنب الحظر
        ydl_opts = {
            'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': False,
            # ✅ إضافة User-Agent لمتصفح حقيقي
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # ✅ إضافة تأخير لتجنب الحظر
            'sleep_interval': 5,
            'max_sleep_interval': 10,
            'sleep_interval_requests': 1,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # محاولة استخراج الرابط
            if 'url' in info:
                download_url = info['url']
            elif 'requested_downloads' in info and len(info['requested_downloads']) > 0:
                download_url = info['requested_downloads'][0]['url']
            else:
                return jsonify({"error": "No download URL found"}), 404
            
            return jsonify({
                "success": True,
                "downloadUrl": download_url,
                "title": info.get('title', 'Video'),
                "author": info.get('uploader', 'Unknown'),
                "duration": info.get('duration', 0)
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# 📊 تحليل الفيديو
# ============================================
@app.route('/api/analyze', methods=['GET'])
def analyze():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "success": True,
                "title": info.get('title', 'Video'),
                "author": info.get('uploader', 'Unknown'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# ✅ التحقق من الصحة
# ============================================
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "timestamp": "2026-08-16T00:00:00Z"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)