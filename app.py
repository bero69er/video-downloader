import yt_dlp
import requests
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

def clean_url(url):
    return url.strip() if url else ""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json()
        url = clean_url(data.get('url', ''))
        
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400

        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check for slideshow/multi-media content
                images = []
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry and entry.get('url'):
                            images.append(entry.get('url'))
                
                # Get the best video URL
                direct_url = info.get('url')
                if not direct_url and info.get('formats'):
                    direct_url = info['formats'][-1].get('url')

                return jsonify({
                    'success': True,
                    'title': info.get('title', 'Media'),
                    'thumbnail': info.get('thumbnail'),
                    'is_slideshow': len(images) > 1,
                    'images': images,
                    'direct_url': direct_url
                })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
            
    return render_template('index.html')

@app.route('/download-file', methods=['GET'])
def download_file():
    target_url = request.args.get('url')
    filename = request.args.get('filename', 'download.mp4')
    
    if not target_url:
        return "Missing URL", 400
        
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = requests.get(target_url, headers=headers, stream=True, timeout=20)
        
        return Response(
            req.iter_content(chunk_size=8192),
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': req.headers.get('Content-Type', 'application/octet-stream')
            }
        )
    except Exception as e:
        return f"Download failed: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
