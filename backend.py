# backend.py

from dotenv import load_dotenv
load_dotenv()

import os
import spotipy
import spotipy.util as util
from transformers import pipeline
from spotipy.oauth2 import SpotifyClientCredentials

# Load emotion classifier
emotion_classifier = pipeline("text-classification", 
                              model="bhadresh-savani/bert-base-uncased-emotion", 
                              return_all_scores=True)

# Load credentials

try:
    import streamlit as st
    SPOTIFY_CLIENT_ID = st.secrets["SPOTIFY_CLIENT_ID"]
    SPOTIFY_CLIENT_SECRET = st.secrets["SPOTIFY_CLIENT_SECRET"]
    SPOTIFY_REDIRECT_URI = st.secrets["SPOTIFY_REDIRECT_URI"]
except:
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
  
print("🔍 SPOTIFY_CLIENT_ID:", repr(SPOTIFY_CLIENT_ID))
print("🔍 SPOTIFY_CLIENT_SECRET:", repr(SPOTIFY_CLIENT_SECRET))

# Spotipy for searching songs (client credentials)
auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID,
                                        client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# 🔍 Detect emotion
def detect_emotion(text):
    results = emotion_classifier(text)[0]
    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    return sorted_results  # List of {label, score}

# 🎵 Get songs based on emotion
def get_songs_by_emotion(emotion, language="english", limit=10):
    lang_to_market = {"english": "US", "hindi": "IN", "bengali": "IN"}
    market = lang_to_market.get(language.lower(), "US")

    query = f"{emotion} mood"
    results = sp.search(q=query, type='track', limit=limit, market=market)
    
    songs = []
    for item in results['tracks']['items']:
        songs.append({
            "name": item['name'],
            "artist": item['artists'][0]['name'],
            "url": item['external_urls']['spotify'],
            "uri": item['uri']
        })
    return songs


# 💾 Create a Spotify playlist in the user's account
def create_spotify_playlist(username, emotion, song_uris):
    scope = "playlist-modify-public"

    # Ask the user to authenticate
    token = util.prompt_for_user_token(
        username=username,
        scope=scope,
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI
    )

    if token:
        user_sp = spotipy.Spotify(auth=token)
        playlist = user_sp.user_playlist_create(user=username,
                                                name=f"My {emotion.title()} Moodboard 🎶",
                                                public=True)
        user_sp.playlist_add_items(playlist_id=playlist['id'], items=song_uris)
        return playlist['external_urls']['spotify']
    else:
        raise Exception("❌ Spotify authentication failed. Check credentials and redirect URI.")
