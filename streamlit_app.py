# streamlit_app.py

import streamlit as st
from backend import detect_emotion, get_songs_by_emotion, create_spotify_playlist
import matplotlib.pyplot as plt

st.set_page_config(page_title="Music Moodboard", layout="wide")

# Lilac background using CSS
st.markdown("""
    <style>
    body {
        background-color: #E6DAF3;
    }
    .big-title {
        font-size: 30px;
        font-weight: bold;
        text-align: center;
        color: #4B0082;
    }
    </style>
""", unsafe_allow_html=True)

# Intro screen
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

if not st.session_state["submitted"]:
    st.markdown('<p class="big-title">Want to create a playlist of your own?</p>', unsafe_allow_html=True)
    user_input = st.text_area("How are you feeling today?", height=200)
    language = st.selectbox("Preferred Language", ["english", "bengali", "hindi"])
    if st.button("Create My Moodboard 🎵"):
        st.session_state["text"] = user_input
        st.session_state["language"] = language
        st.session_state["submitted"] = True
        st.rerun()
else:
    user_input = st.session_state["text"]
    language = st.session_state["language"]

    # Detect emotions only once and store
    if "emotion_scores" not in st.session_state:
        emotion_scores = detect_emotion(user_input)
        st.session_state["emotion_scores"] = emotion_scores
    else:
        emotion_scores = st.session_state["emotion_scores"]

    labels = [e['label'] for e in emotion_scores]
    scores = [round(e['score'] * 100, 2) for e in emotion_scores]
    top_emotion = labels[0]

    # Playlist toggle state
    if "show_playlist" not in st.session_state:
        st.session_state["show_playlist"] = False

    # Show emotion graph only before playlist is displayed
    if not st.session_state["show_playlist"]:
        st.subheader("🎭 Detected Emotions (with confidence)")
        fig, ax = plt.subplots()
        ax.barh(labels[::-1], scores[::-1], color="#BA55D3")
        st.pyplot(fig)

        if st.button("🎧 Show me my vibe playlist!"):
            st.session_state["show_playlist"] = True
            st.rerun()

    # Show playlist only after button is clicked
    else:
        st.markdown(f"### ✨ Playlist for your **{top_emotion}** mood ✨")
        songs = get_songs_by_emotion(top_emotion, language=language)

        for i, song in enumerate(songs, 1):
            st.markdown(f"""
            <div style="padding:10px; background-color:#f3e9ff; border-radius:10px; margin-bottom:10px">
                <b>{i}. {song['name']}</b> – <i>{song['artist']}</i><br>
                🎵 <a href="{song['url']}" target="_blank">Listen on Spotify</a>
            </div>
            """, unsafe_allow_html=True)

        # 🎯 Extract track URIs for adding to playlist
        track_uris = [song['url'].split("/")[-1] for song in songs]  # extract track IDs
        track_uris = [f"spotify:track:{track_id}" for track_id in track_uris]

        # Prompt user for Spotify username
        username = st.text_input("Enter your Spotify username to save this playlist:")

        if st.button("💾 Save playlist to my Spotify"):
            try:
                playlist_url = create_spotify_playlist(username, top_emotion, track_uris)
                st.success("✅ Playlist created successfully!")
                st.markdown(f"[🎧 Open Your Playlist Here]({playlist_url})")
            except Exception as e:
                st.error(f"Something went wrong: {e}")
