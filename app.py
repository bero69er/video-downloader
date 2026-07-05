import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def clean_url(url):
    return url.strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            url = clean_url(data.get('url', ''))
        else:
            url = clean_url(request.form.get('url', ''))

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        try:
            import yt_dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return jsonify({'error': 'Failed to extract media details'}), 400
                
                # Extract image slides if available
                images = []
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry and entry.get('url'):
                            images.append(entry.get('url'))
                elif info.get('formats'):
                    # Check for raw image formats inside entries
                    for f in info['formats']:
                        if f.get('ext') in ['jpg', 'jpeg', 'png', 'webp'] or 'image' in f.get('format', ''):
                            images.append(f.get('url'))

                # Custom parsing logic to fix missing thumbnails
                thumbnail = info.get('thumbnail')
                if not thumbnail and info.get('thumbnails'):
                    thumbnail = info['thumbnails'][-1].get('url')
                
                # If it's TikTok, grab the cover or dynamic cover if normal thumbnail is missing
                if not thumbnail and 'tiktok' in url.lower():
                    thumbnail = info.get('cover') or info.get('dynamic_cover')
                
                # Default fallback placeholder image if completely blocked by scraping limits
                if not thumbnail:
                    thumbnail = "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"

                is_slideshow = len(images) > 1
                
                # Extract best standalone single video link for automatic downloads
                direct_url = None
                if not is_slideshow:
                    # Select premium streaming link directly
                    direct_url = info.get('url')
                    if not direct_url and info.get('formats'):
                        # Look for standard pre-muxed video formats with sound active
                        valid_formats = [f for f in info['formats'] if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                        if valid_formats:
                            direct_url = valid_formats[-1].get('url')
                        else:
                            direct_url = info['formats'][-1].get('url')

                return jsonify({
                    'success': True,
                    'title': info.get('title', 'Media Asset'),
                    'thumbnail': thumbnail,
                    'is_slideshow': is_slideshow,
                    'images': images,
                    'direct_url': direct_url
                })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
