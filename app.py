import json
from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import requests
from urllib.parse import urlparse
import mimetypes
import os

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Helper to detect if URL is a direct image
def is_direct_image(url):
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif')
    parsed = urlparse(url.lower())
    return any(parsed.path.endswith(ext) for ext in image_extensions)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preview', methods=['POST'])
def preview():
    """Returns thumbnail and media info before downloading"""
    data = request.get_json()
    url = data.get('url')
    
    try:
        # For direct images, return immediately
        if is_direct_image(url):
            return jsonify({
                'type': 'image',
                'thumbnail': url,
                'items': [{'url': url, 'type': 'image'}]
            })
        
        # For videos/slideshows, extract info without downloading
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check for TikTok slideshows / multiple images
            items = []
            if 'entries' in info:  # Playlist or slideshow
                for entry in info['entries']:
                    items.append({
                        'url': entry.get('url') or entry.get('webpage_url'),
                        'type': 'image' if entry.get('_type') == 'image' else 'video',
                        'thumb': entry.get('thumbnail')
                    })
            else:
                items.append({
                    'url': info.get('webpage_url', url),
                    'type': 'video',
                    'thumb': info.get('thumbnail')
                })
            
            return jsonify({
                'type': 'mixed' if len(items) > 1 else 'video',
                'thumbnail': info.get('thumbnail'),
                'title': info.get('title'),
                'items': items
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['POST'])
def download():
    """Handles actual file download"""
    data = request.get_json()
    url = data.get('url')
    media_type = data.get('type', 'video')  # video, image, audio
    format_choice = data.get('format', 'mp4')
    
    try:
        # Handle direct image download
        if is_direct_image(url) or media_type == 'image':
            response = requests.get(url, stream=True)
            filename = os.path.basename(urlparse(url).path) or f'image_{os.urandom(4).hex()}.jpg'
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return send_file(filepath, as_attachment=True)
        
        # Handle video/audio with yt-dlp
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'restrictfilenames': True,
            'noplaylist': True,
        }
        
        if format_choice == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format_choice == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
        
        return send_file(filename, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
