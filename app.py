import os
import requests
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

def clean_url(url):
    return url.strip() if url else ""

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
                
                # Gather images/slideshow tracks
                images = []
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry and entry.get('url'):
                            images.append(entry.get('url'))
                elif info.get('formats'):
                    for f in info['formats']:
                        if f.get('ext') in ['jpg', 'jpeg', 'png', 'webp'] or 'image' in f.get('format', ''):
                            images.append(f.get('url'))

                # Parse correct thumbnail previews
                thumbnail = info.get('thumbnail')
                if not thumbnail and info.get('thumbnails'):
                    thumbnail = info['thumbnails'][-1].get('url')
                
                if not thumbnail and 'tiktok' in url.lower():
                    thumbnail = info.get('cover') or info.get('dynamic_cover')
                
                if not thumbnail:
                    thumbnail = "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500"

                is_slideshow = len(images) > 1
                
                # Parse optimal video asset address pathing
                direct_url = None
                if not is_slideshow:
                    direct_url = info.get('url')
                    if not direct_url and info.get('formats'):
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


# NEW STREAM PROXY ROUTE: Pulls the data cleanly through the server to bypass browser download blocking
@app.route('/download-file', methods=['GET'])
def download_file():
    target_url = request.args.get('url')
    filename = request.args.get('filename', 'download.mp4')
    
    if not target_url:
        return "Missing resource target link configuration parameter.", 400
        
    try:
        # Request stream contents straight from resource distribution endpoints
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        req = requests.get(target_url, headers=headers, stream=True, timeout=25)
        
        # Build streamed system attachment delivery channel parameters
        response_headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': req.headers.get('Content-Type', 'application/octet-stream')
        }
        
        return Response(req.iter_content(chunk_size=4096), headers=response_headers, status=req.status_code)
    except Exception as e:
        return f"Secure proxy transfer pipeline distribution initialization error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
