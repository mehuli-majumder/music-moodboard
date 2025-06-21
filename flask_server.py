# flask_server.py

from flask import Flask, request, redirect, session
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Needed for session

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="playlist-modify-public",
    cache_path=".cache-web",  # Optional
    show_dialog=True
)

@app.route("/")
def home():
    return "🎵 Flask server is running and ready to handle Spotify redirects!"

@app.route("/login")
def login():
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_info = auth_manager.get_access_token(code, as_dict=True)
    access_token = token_info["access_token"]

    # Store access token in session
    session["access_token"] = access_token

    return f"""
    ✅ Authorization complete. You can close this tab and return to the app.
    <script>
        localStorage.setItem("spotify_token", "{access_token}");
    </script>
    """

@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    access_token = session.get("access_token")
    if not access_token:
        return {"error": "Not authenticated"}, 401

    sp = Spotify(auth=access_token)
    data = request.json
    username = sp.me()["id"]
    songs = data.get("tracks", [])

    playlist = sp.user_playlist_create(user=username, name="My Music Moodboard 🎧", public=True)
    sp.playlist_add_items(playlist_id=playlist["id"], items=songs)

    return {"playlist_url": playlist["external_urls"]["spotify"]}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
