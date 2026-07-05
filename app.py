# Your original Python code - NO CHANGES NEEDED
import os
from flask import Flask, render_template, request, send_file
import yt_dlp

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form.get('url')
        requested_format = request.form.get('format')

        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'restrictfilenames': True,
            'noplaylist': True,
        }

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
                
                if requested_format == 'mp3':
                    filename = os.path.splitext(filename)[0] + '.mp3'

            return send_file(filename, as_attachment=True)

        except Exception as e:
            return f"An error occurred during extraction processing: {str(e)}", 400

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
