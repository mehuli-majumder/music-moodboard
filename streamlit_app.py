import streamlit as st
from backend import detect_emotion, get_songs_by_emotion
import matplotlib.pyplot as plt
import requests

# BACKEND_URL = "https://music-moodboard.onrender.com"

BACKEND_URL = st.secrets["BACKEND_URL"]

st.set_page_config(page_title="Music Moodboard", layout="wide")

st.markdown("""
    <style>
    body {
        background: linear-gradient(120deg, #E6DAF3, #fdf0ff);
        animation: backgroundMove 30s infinite alternate;
    }

    @keyframes backgroundMove {
        0% {background-position: 0% 50%;}
        100% {background-position: 100% 50%;}
    }

    .big-title {
        font-size: 32px;
        font-weight: bold;
        text-align: center;
        color: #6A0DAD;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% {transform: scale(1);}
        50% {transform: scale(1.05);}
        100% {transform: scale(1);}
    }

    button[kind="primary"] {
        background-color: #BA55D3;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
    }

    div[data-testid="stMarkdownContainer"] a:hover {
        color: #8A2BE2;
    }
    </style>
""", unsafe_allow_html=True)

# States
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "show_playlist" not in st.session_state:
    st.session_state["show_playlist"] = False
if "track_uris" not in st.session_state:
    st.session_state["track_uris"] = []
if "top_emotion" not in st.session_state:
    st.session_state["top_emotion"] = ""

# Intro screen
if not st.session_state["submitted"]:
    st.markdown('<p class="big-title">Want to create a playlist of your own?</p>', unsafe_allow_html=True)
    user_input = st.text_area("How are you feeling today?", height=200)
    language = st.selectbox("Preferred Language", ["english", "bengali", "hindi"])
    if st.button("Create My Moodboard 🎵") and user_input:
        st.session_state["text"] = user_input
        st.session_state["language"] = language
        st.session_state["submitted"] = True
        st.rerun()

else:
    user_input = st.session_state["text"]
    language = st.session_state["language"]

    # Detect emotions
    if "emotion_scores" not in st.session_state:
        emotion_scores = detect_emotion(user_input)
        st.session_state["emotion_scores"] = emotion_scores
    else:
        emotion_scores = st.session_state["emotion_scores"]

    labels = [e['label'] for e in emotion_scores]
    scores = [round(e['score'] * 100, 2) for e in emotion_scores]
    top_emotion = labels[0]
    st.session_state["top_emotion"] = top_emotion

    if not st.session_state["show_playlist"]:
        st.subheader("🎝 Detected Emotions")
        fig, ax = plt.subplots()
        ax.barh(labels[::-1], scores[::-1], color="#BA55D3")
        st.pyplot(fig)

        if st.button("🎷 Show me my vibe playlist!"):
            st.session_state["show_playlist"] = True
            st.rerun()

    else:
        st.markdown(f"### ✨ MoodBoard ✨")
        songs = get_songs_by_emotion(top_emotion, language=language)

        track_uris = []
        for i, song in enumerate(songs, 1):
            st.markdown(f"""
            <div style="padding:10px; background-color:#f3e9ff; border-radius:10px; margin-bottom:10px">
                <b>{i}. {song['name']}</b> – <i>{song['artist']}</i><br>
                🎵 <a href="{song['url']}" target="_blank">Listen on Spotify</a>
            </div>
            """, unsafe_allow_html=True)
            track_id = song['url'].split("/")[-1].split("?")[0]
            track_uris.append(f"spotify:track:{track_id}")

        st.session_state["track_uris"] = track_uris

        playlist_name = st.text_input("📝 Name your playlist", value=f"{top_emotion.title()} Vibes 🎧")

        if st.button("📎 Generate Playlist Link"):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/create_playlist",
                    json={
                        "emotion": playlist_name,
                        "track_uris": st.session_state["track_uris"]
                    },
                    timeout=15
                )

                if res.status_code == 200:
                    playlist_url = res.json().get("playlist_url")
                    st.success("✅ Playlist created successfully!")
                    st.markdown(f"🎧 [Click here to open your playlist on Spotify]({playlist_url})")
                    st.info("🎵 Liked your playlist? Just tap Add to Playlist on Spotify to keep it")
                else:
                    error_detail = res.json().get("error", "No error info")
                    st.error(f"❌ Failed to create playlist: {error_detail}")
            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")
