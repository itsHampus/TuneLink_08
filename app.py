import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for
from spotipy import Spotify
from spotipy.cache_handler import CacheFileHandler, FlaskSessionCacheHandler
from spotipy.oauth2 import SpotifyOAuth
from db import get_connection


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

scope = os.getenv("SPOTIPY_SCOPE")


@app.route("/")
def index():
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope=scope,
        cache_handler=FlaskSessionCacheHandler(session),
        show_dialog=True,
    )
    auth_url = auth_manager.get_authorize_url()
    return render_template("index.html", auth_url=auth_url)


@app.route("/callback")
def callback():
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope=scope,
        cache_handler=FlaskSessionCacheHandler(session),
        show_dialog=True,
    )
    code = request.args.get("code")
    token_info = auth_manager.get_access_token(code)
    session["token_info"] = token_info

    sp = Spotify(auth=token_info["access_token"])
    profile = sp.current_user()

    spotify_id = profile["id"]
    display_name = profile["display_name"] or "Anonym"

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM users WHERE spotify_id = %s", (spotify_id,))
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO users(spotify_id, username) VALUES (%s,%s) RETURNING id;",
            (spotify_id, display_name)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
    else:
        user_id = user[0]

    cur.close()
    conn.close()
    session["user_id"] = user_id
    return redirect(url_for("profile"))


@app.route("/profile")
def profile():
    token_info = session.get("token_info")
    if not token_info:
        return redirect(url_for("index"))

    sp = Spotify(auth=token_info["access_token"])

    user = sp.current_user()

    top_tracks_raw = sp.current_user_top_tracks(limit=5, time_range="short_term")[
        "items"
    ]
    top_tracks = [
        {"name": t["name"], "artists": t["artists"][0]} for t in top_tracks_raw
    ]

    top_artists_raw = sp.current_user_top_artists(limit=5, time_range="short_term")[
        "items"
    ]
    top_artists = [
        {"name": a["name"], "genres": a["genres"][0] if a["genres"] else "unknown"}
        for a in top_artists_raw
    ]

    genre_list = []
    for artists in top_artists_raw:
        genre_list.extend(artists["genres"])
    top_genres = sorted(set(genre_list))[:5]

    return render_template(
        "profile.html",
        user=user,
        top_tracks=top_tracks,
        top_artists=top_artists,
        genres=top_genres,
    )


@app.route("/logout")
def logout():
    cache_handler = CacheFileHandler(cache_path=".cache")
    if os.path.exists(".cache"):
        os.remove(".cache")
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
