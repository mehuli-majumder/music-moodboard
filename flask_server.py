from flask import Flask, request, redirect, jsonify
from flask_cors import CORS
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
import json
import base64
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

app = Flask(__name__)
CORS(app)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# Use local path (non-persistent) + fallback to encoded env token
DISK_PATH = "."
TOKEN_PATH = os.path.join(DISK_PATH, "access_token.json")
CACHE_PATH = os.path.join(DISK_PATH, ".cache-web")

auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="playlist-modify-public playlist-modify-private",
    cache_path=CACHE_PATH,
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

    # Save token locally (optional short-term)
    with open(TOKEN_PATH, "w") as f:
        json.dump(token_info, f)

    # Print base64 token for storing in Render environment manually
    encoded_token = base64.b64encode(json.dumps(token_info).encode()).decode()
    print("\n\u2728 Add this to your Render ENV as SPOTIFY_TOKEN:\n")
    print(encoded_token)
    print("\n")

    return "✅ Authorization complete. You can close this tab."

@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    try:
        # Try loading from file
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "r") as f:
                token_info = json.load(f)
        else:
            # Fallback to Render ENV
            encoded_token = os.getenv("SPOTIFY_TOKEN")
            if not encoded_token:
                return jsonify({"error": "No access token. Please login."}), 401
            token_info = json.loads(base64.b64decode(encoded_token.encode()).decode())

        # Refresh if needed
        if auth_manager.is_token_expired(token_info):
            token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
            with open(TOKEN_PATH, "w") as f:
                json.dump(token_info, f)

        access_token = token_info["access_token"]
        sp = Spotify(auth=access_token)

        data = request.get_json()
        print("Received data:", data)

        track_uris = data.get("track_uris") or data.get("songs") or []
        playlist_name = data.get("emotion", "My Moodboard")

        if not track_uris:
            return jsonify({"error": "No tracks provided"}), 400

        user_id = sp.me()["id"]
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
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