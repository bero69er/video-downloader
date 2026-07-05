import os
from flask import Flask, render_template, request, send_file
import yt_dlp

app = Flask(__name__)

# Configures the storage directory for downloaded files on your server
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form.get('url')
        requested_format = request.form.get('format')  # Grabs 'mp4' or 'mp3' from the frontend

        # Global layout configuration rules for the engine
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'restrictfilenames': True,
            'noplaylist': True,
        }

        # Adjust formatting parameters on the fly based on user selection
        if requested_format == 'mp3':
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

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Resolves the exact system extension if audio post-processing occurred
                if requested_format == 'mp3':
                    filename = os.path.splitext(filename)[0] + '.mp3'

            # Packages and streams the target file right to the iOS download manager folder
            return send_file(filename, as_attachment=True)

        except Exception as e:
            return f"An error occurred during extraction processing: {str(e)}", 400

    return render_template('index.html')

if __name__ == '__main__':
    # Binds server directly to local loopback ports for development testing
    app.run(debug=True)
