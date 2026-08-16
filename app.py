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
        # إعدادات مرنة للحصول على أفضل تنسيق متاح
        ydl_opts = {
            'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': False,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # ✅ إذا لم يجد التنسيق المطلوب، حاول الحصول على أفضل تنسيق متاح
            if not info:
                return jsonify({"error": "No video info found"}), 404
            
            # محاولة استخراج الرابط
            download_url = None
            
            # 1. حاول الحصول على الرابط المباشر
            if 'url' in info and info['url']:
                download_url = info['url']
            
            # 2. حاول الحصول من requested_downloads
            elif 'requested_downloads' in info and info['requested_downloads']:
                for item in info['requested_downloads']:
                    if 'url' in item and item['url']:
                        download_url = item['url']
                        break
            
            # 3. حاول الحصول من formats (آخر حل)
            elif 'formats' in info and info['formats']:
                # اختر أفضل تنسيق فيديو+صوت
                for fmt in info['formats']:
                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') != 'none':
                        if 'url' in fmt and fmt['url']:
                            download_url = fmt['url']
                            break
                
                # إذا لم نجد فيديو+صوت، خذ أي فيديو
                if not download_url:
                    for fmt in info['formats']:
                        if fmt.get('vcodec') != 'none' and 'url' in fmt and fmt['url']:
                            download_url = fmt['url']
                            break
            
            if not download_url:
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
            
            # استخراج التنسيقات المتاحة
            formats = []
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('vcodec') != 'none' or fmt.get('acodec') != 'none':
                        formats.append({
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'quality': fmt.get('quality'),
                            'height': fmt.get('height'),
                            'width': fmt.get('width'),
                            'fps': fmt.get('fps'),
                            'vcodec': fmt.get('vcodec'),
                            'acodec': fmt.get('acodec'),
                        })
            
            return jsonify({
                "success": True,
                "title": info.get('title', 'Video'),
                "author": info.get('uploader', 'Unknown'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
                "formats": formats[:20]  # إرجاع أول 20 تنسيق
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)