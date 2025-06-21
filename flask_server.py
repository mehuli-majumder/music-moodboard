# flask_server.py

import os
from flask import Flask, request, redirect
from dotenv import load_dotenv
import spotipy.util as util

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Spotify credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

@app.route('/')
def home():
    return "🎵 Flask server is running and ready to handle Spotify redirects!"

@app.route('/login')
def login():
    username = request.args.get("username")
    if not username:
        return "⚠️ Missing username in /login?username=... query param", 400

    scope = "playlist-modify-public"

    try:
        auth_url = util.prompt_for_user_token(
            username=username,
            scope=scope,
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            show_dialog=True
        )
        return redirect(auth_url or "/error")

    except Exception as e:
        return f"❌ Error during Spotify login: {str(e)}", 500

@app.route('/callback')
def callback():
    return "✅ Spotify authorization complete! You can close this tab and go back to the app."

if __name__ == "__main__":
    # Render provides the port via an environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
