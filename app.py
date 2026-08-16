import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ============================================
# 📋 إعدادات yt-dlp المتقدمة
# ============================================
YDL_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'cookiefile': 'cookies.txt',
    'ignoreerrors': True,
    'extract_flat': False,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    },
    # استراتيجيات متعددة لتجاوز الحظر
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web', 'ios'],
            'skip': ['dash', 'hls'],
        }
    }
}

# ============================================
# 📥 تحميل الفيديو
# ============================================
@app.route('/api/download', methods=['GET'])
def download():
    url = request.args.get('url')
    quality = request.args.get('quality', '720')
    
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    try:
        # استراتيجيات متعددة للحصول على الرابط
        strategies = [
            # الاستراتيجية 1: فيديو + صوت مدمج
            {
                'name': 'bestvideo+bestaudio',
                'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            },
            # الاستراتيجية 2: أي فيديو مع الصوت
            {
                'name': 'best',
                'format': 'best'
            },
            # الاستراتيجية 3: فيديو فقط (بدون صوت) - كحل أخير
            {
                'name': 'bestvideo',
                'format': f'bestvideo[height<={quality}][ext=mp4]'
            }
        ]
        
        last_error = None
        
        for strategy in strategies:
            try:
                ydl_opts = YDL_OPTS.copy()
                ydl_opts['format'] = strategy['format']
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        continue
                    
                    download_url = None
                    
                    # محاولة استخراج الرابط بطرق مختلفة
                    if 'url' in info and info['url']:
                        download_url = info['url']
                    elif 'requested_downloads' in info and info['requested_downloads']:
                        for item in info['requested_downloads']:
                            if 'url' in item and item['url']:
                                download_url = item['url']
                                break
                    elif 'formats' in info and info['formats']:
                        for fmt in info['formats']:
                            if fmt.get('vcodec') != 'none' and 'url' in fmt and fmt['url']:
                                download_url = fmt['url']
                                break
                    
                    if download_url:
                        return jsonify({
                            "success": True,
                            "downloadUrl": download_url,
                            "title": info.get('title', 'Video'),
                            "author": info.get('uploader', 'Unknown'),
                            "duration": info.get('duration', 0),
                            "strategy": strategy['name']
                        })
                        
            except Exception as e:
                last_error = str(e)
                continue
        
        # إذا فشلت جميع الاستراتيجيات
        return jsonify({
            "error": f"فشل تحميل الفيديو. حاول مرة أخرى. الخطأ: {last_error}",
            "hint": "تأكد من تحديث ملف cookies.txt"
        }), 503
        
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
            'cookiefile': 'cookies.txt',
            'headers': YDL_OPTS['headers'],
            'extractor_args': YDL_OPTS['extractor_args']
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({"error": "No video info found"}), 404
            
            # استخراج التنسيقات المتاحة
            formats = []
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('vcodec') != 'none' or fmt.get('acodec') != 'none':
                        formats.append({
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'height': fmt.get('height'),
                            'width': fmt.get('width'),
                            'acodec': fmt.get('acodec'),
                            'vcodec': fmt.get('vcodec'),
                            'fps': fmt.get('fps'),
                        })
            
            return jsonify({
                "success": True,
                "title": info.get('title', 'Video'),
                "author": info.get('uploader', 'Unknown'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
                "formats": formats[:20]
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
        "timestamp": "2026-08-16T00:00:00Z",
        "platforms": ["youtube", "facebook", "tiktok", "instagram", "twitter"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)