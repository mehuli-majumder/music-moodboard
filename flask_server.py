from flask import Flask, request, redirect, jsonify
from flask_cors import CORS
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="playlist-modify-public playlist-modify-private",
    cache_path=".cache-web",
    show_dialog=True
)

@app.route("/")
def home():
    return "🎵 Flask server is running!"

@app.route("/login")
def login():
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_info = auth_manager.get_access_token(code, as_dict=True)

    if not token_info:
        return "❌ Failed to get token."

    with open("access_token.json", "w") as f:
        json.dump(token_info, f)

    return "✅ Authorization complete. You can close this tab."

@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    try:
        if not os.path.exists("access_token.json"):
            return jsonify({"error": "No access token. Please login."}), 401

        with open("access_token.json", "r") as f:
            token_info = json.load(f)

        if auth_manager.is_token_expired(token_info):
            token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
            with open("access_token.json", "w") as f:
                json.dump(token_info, f)

        access_token = token_info["access_token"]
        sp = Spotify(auth=access_token)

        data = request.get_json()
        print("Received data:", data)

        # Accept both 'track_uris' or 'songs' keys
        track_uris = data.get("track_uris") or data.get("songs") or []
        emotion = data.get("emotion", "My Moodboard")

        if not track_uris:
            return jsonify({"error": "No tracks provided"}), 400

        user_id = sp.me()["id"]
        playlist = sp.user_playlist_create(
            user=user_id,
            name=f"{emotion.title()} Vibes 🎧",
            public=True,
            description="Created using Music Moodboard ✨"
        )

        sp.playlist_add_items(playlist_id=playlist["id"], items=track_uris)

        return jsonify({
            "success": True,
            "playlist_url": playlist["external_urls"]["spotify"]
        })

    except Exception as e:
        print("Error during playlist creation:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
