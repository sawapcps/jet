import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "timestamp": "2026-08-16T00:00:00Z"})

@app.route('/api/download', methods=['GET'])
def download():
    url = request.args.get('url')
    quality = request.args.get('quality', '720')
    
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    try:
        # إعدادات yt-dlp محسنة
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': False,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'cookiefile': 'cookies.txt',  # تأكد من وجود هذا الملف
            'format': 'best',  # اختر أفضل تنسيق بشكل افتراضي
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # محاولة استخراج المعلومات
            info = ydl.extract_info(url, download=False)
            
            # إذا لم يتم العثور على معلومات
            if not info:
                return jsonify({"error": "No video info found. Please check the URL."}), 404
            
            # محاولة الحصول على رابط التحميل
            download_url = None
            
            # 1. حاول من 'url'
            if 'url' in info and info['url']:
                download_url = info['url']
            
            # 2. حاول من 'requested_downloads'
            elif 'requested_downloads' in info and info['requested_downloads']:
                for item in info['requested_downloads']:
                    if 'url' in item and item['url']:
                        download_url = item['url']
                        break
            
            # 3. حاول من 'formats'
            elif 'formats' in info and info['formats']:
                # ابحث عن تنسيق فيديو+صوت
                for fmt in info['formats']:
                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') != 'none' and 'url' in fmt and fmt['url']:
                        download_url = fmt['url']
                        break
                
                # إذا لم يتم العثور على فيديو+صوت، اختر أي فيديو
                if not download_url:
                    for fmt in info['formats']:
                        if fmt.get('vcodec') != 'none' and 'url' in fmt and fmt['url']:
                            download_url = fmt['url']
                            break
            
            # إذا لم يتم العثور على رابط
            if not download_url:
                return jsonify({"error": "No download URL found. Video may be restricted."}), 404
            
            # إرجاع النتيجة
            return jsonify({
                "success": True,
                "downloadUrl": download_url,
                "title": info.get('title', 'Video'),
                "author": info.get('uploader', 'Unknown'),
                "duration": info.get('duration', 0)
            })
            
    except Exception as e:
        # إرجاع تفاصيل الخطأ للمساعدة في التشخيص
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['GET'])
def analyze():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'cookiefile': 'cookies.txt',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({"error": "No video info found. Please check the URL."}), 404
            
            return jsonify({
                "success": True,
                "title": info.get('title', 'Video'),
                "author": info.get('uploader', 'Unknown'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)