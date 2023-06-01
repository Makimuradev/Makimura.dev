import os
import requests
import io
import numpy as np
from flask import Flask, request, jsonify, redirect, abort, session, render_template
from concurrent.futures import ThreadPoolExecutor
from waitress import serve
 
from scipy.signal import resample
from scipy.io import wavfile
import time
import whisper
import soundfile as sf
import datetime
from flask_cors import CORS
import threading
from flask import make_response
import subprocess
import tempfile
from scipy.signal import resample_poly

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
executor = ThreadPoolExecutor(max_workers=5)

model = whisper.load_model("tiny.en.pt")
api_key = os.environ.get("API_KEY")

def require_api_key(func):
    def wrapper(*args, **kwargs):
        if "X-API-Key" not in request.headers or request.headers["X-API-Key"] != api_key:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route("/recaptcha", methods=["POST"])
@require_api_key
def recaptcha_endpoint():
    if request.method == "POST":
        # Receive the audio stream URL from the request
        audio_stream_url = request.json.get("audio_stream_url")

        retries = 3
        retry_delay = 10

        for attempt in range(retries):
            try:
                future = executor.submit(transcribe_audio, audio_stream_url)
                transcription = future.result()
                response = {"transcription": transcription}
                return jsonify(response)
            except Exception as e:
                error_message = f"Error occurred: {e}"

                if attempt < retries - 1:
                    error_message += f" Retrying after {retry_delay} seconds..."
                    retry_delay *= 2
                    time.sleep(retry_delay)

                return jsonify({"error": error_message}), 500

    # Return an error response for unsupported HTTP methods
    return jsonify({"error": "Unsupported method"}), 405


@app.route("/recaptcha", methods=["GET"])
def recaptcha_redirect1():
    return redirect("https://makimura.dev", code=302)

@app.route("/", methods=["GET"])
def verify_endpoint():
    return render_template("index.html")
  
def transcribe_audio(audio_stream_url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        response = requests.get(audio_stream_url, headers=headers, stream=False)
        response.raise_for_status()

        # Save the audio data to a temporary file
        script_dir = os.path.dirname(os.path.realpath(__file__))
        with tempfile.NamedTemporaryFile(delete=False, dir=script_dir, suffix=".mp3") as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)

        temp_file_path = temp_file.name

         

        # Perform transcription using the whisper
        transcription = model.transcribe("./" + temp_file_path, verbose=True )

        result = transcription["text"].strip()

        # Delete the temporary files
        os.remove(temp_file_path)
         

        return result
    except requests.exceptions.RequestException as e:
        return f"Error occurred while fetching audio: {str(e)}"
    except subprocess.CalledProcessError:
        return "Error occurred during audio conversion"
    except KeyError:
        return "Error occurred during transcription"

 



def create_app():
    return app

if __name__ == "__main__":
    print("Server started")
    serve(app, host='0.0.0.0', port=8000)




