import os
import re
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

# Ensure download folder exists
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def clean_url(url):
    return url.strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if it's an AJAX fetch request
        if request.is_json:
            data = request.get_json()
            url = clean_url(data.get('url', ''))
            fmt = data.get('format', 'mp4')
        else:
            url = clean_url(request.form.get('url', ''))
            fmt = request.form.get('format', 'mp4')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'allowed_extractors': ['.*'],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check for TikTok photo slideshows / images
                images = []
                if 'entries' in info:
                    # Playlist/slideshow structure
                    for entry in info['entries']:
                        if entry.get('url') and entry.get('ext') in ['jpg', 'jpeg', 'png', 'webp']:
                            images.append(entry.get('url'))
                elif info.get('requested_downloads'):
                    for d in info['requested_downloads']:
                        if d.get('ext') in ['jpg', 'jpeg', 'png', 'webp'] or 'image' in d.get('format', ''):
                            images.append(d.get('url'))
                
                # Fallback check for raw images in info dict
                if not images and info.get('ext') in ['jpg', 'jpeg', 'png', 'webp']:
                    images.append(info.get('url'))
                
                thumbnail = info.get('thumbnail') or info.get('thumbnails', [{}])[-1].get('url', '')
                
                # Determine type
                is_slideshow = len(images) > 0
                
                # Respond back to frontend asynchronously
                return jsonify({
                    'success': True,
                    'title': info.get('title', 'Media'),
                    'thumbnail': thumbnail,
                    'is_slideshow': is_slideshow,
                    'images': images,
                    'direct_url': info.get('url') if not is_slideshow else None
                })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return render_template('index.html')

# Endpoint to safely handle direct media streaming/downloads if needed
@app.route('/stream-file')
def stream_file():
    file_url = request.args.get('url')
    if not file_url:
        return "Missing media URL", 400
    # Redirect directly to streaming CDN asset safely
    return f"<script>window.location.href='{file_url}';</script>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
