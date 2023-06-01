import requests
import json

SERVER_URL = "http://localhost:8000"
RECAPTCHA_ENDPOINT = "/recaptcha"
API_KEY = "hello"  # Replace with your API key

AUDIO_FILE_URL = "https://www.wavsource.com/snds_2020-10-01_3728627494378403/sfx/woow_x.wav"

session = requests.Session()

def send_post_request(audio_file_url):
    url = f"{SERVER_URL}{RECAPTCHA_ENDPOINT}"

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY  # Include the API key in the headers
    }
    data = {"audio_stream_url": audio_file_url}
    response = session.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        result = response.json()
        transcription = result.get("transcription")
        if transcription:
            print("Transcription:", transcription)
        else:
            print("Error: Invalid response format")
    else:
        print("Error:", "You're probably being rate limited..",response.text)

send_post_request(AUDIO_FILE_URL)
