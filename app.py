# app.py - النسخة النهائية مع دعم يوتيوب وفيسبوك وتيك توك
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
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'cookiefile': 'cookies.txt',
    # 🔑 تقليد متصفح حقيقي لتجاوز الحظر
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    },
    # إعدادات إضافية لتجنب الحظر
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
        },
        'tiktok': {
            'api_hostname': 'www.tiktok.com',
        }
    }
}

# ============================================
# 🔍 كشف المنصة
# ============================================
def detect_platform(url):
    url_lower = url.lower()
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
        return 'facebook'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    else:
        return 'unknown'

# ============================================
# 📥 تحميل الفيديو
# ============================================
@app.route('/api/download', methods=['GET'])
def download():
    url = request.args.get('url')
    quality = request.args.get('quality', '720')
    
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    platform = detect_platform(url)
    
    try:
        # نسخ الإعدادات الأساسية
        ydl_opts = YDL_OPTS.copy()
        
        # إعدادات خاصة بالجودة
        if quality.isdigit():
            ydl_opts['format'] = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            ydl_opts['format'] = 'best'
        
        # إعدادات خاصة بالمنصة
        if platform == 'tiktok':
            ydl_opts['extractor_args'] = {
                'tiktok': {
                    'api_hostname': 'www.tiktok.com',
                }
            }
            # تيك توك يحتاج إلى cookies قوية
            ydl_opts['cookiefile'] = 'cookies.txt'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({"error": "No video info found"}), 404
            
            # استخراج الرابط
            download_url = None
            
            if 'url' in info and info['url']:
                download_url = info['url']
            elif 'requested_downloads' in info and info['requested_downloads']:
                for item in info['requested_downloads']:
                    if 'url' in item and item['url']:
                        download_url = item['url']
                        break
            elif 'formats' in info and info['formats']:
                for fmt in info['formats']:
                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') != 'none' and 'url' in fmt and fmt['url']:
                        download_url = fmt['url']
                        break
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
                "duration": info.get('duration', 0),
                "platform": platform,
                "quality": quality
            })
            
    except Exception as e:
        error_msg = str(e)
        # رسائل خطأ مخصصة للمنصات
        if 'tiktok' in error_msg.lower() or '403' in error_msg:
            return jsonify({
                "error": "تيك توك صعب التحميل. حاول استخدام تطبيق تيك توك",
                "platform": "tiktok",
                "suggestion": "Use TikTok app or try again later"
            }), 403
        elif 'facebook' in error_msg.lower():
            return jsonify({
                "error": "فشل تحميل فيديو فيسبوك. تأكد من الرابط",
                "platform": "facebook"
            }), 400
        else:
            return jsonify({"error": error_msg}), 500

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
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({"error": "No video info found"}), 404
            
            return jsonify({
                "success": True,
                "title": info.get('title', 'Video'),
                "author": info.get('uploader', 'Unknown'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
                "platform": detect_platform(url),
                "formats": [
                    {
                        'quality': f"{fmt.get('height', 'audio')}p" if fmt.get('height') else 'audio',
                        'ext': fmt.get('ext', 'mp4'),
                        'filesize': fmt.get('filesize', 0),
                        'format_id': fmt.get('format_id'),
                    }
                    for fmt in info.get('formats', [])[:10]
                ]
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