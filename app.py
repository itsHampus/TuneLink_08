import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for
from spotipy import Spotify
from spotipy.cache_handler import CacheFileHandler, FlaskSessionCacheHandler
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from flask import flash

import db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

scope = os.getenv("SPOTIPY_SCOPE")

@app.context_processor
def inject_user():
    user = None
    user_image = url_for('static', filename='default_profile.png')

    token_info = session.get("token_info")
    if token_info:
        try:
            sp = Spotify(auth=token_info["access_token"])
            user = sp.current_user()
            if user and user.get("images"):
                user_image = user["images"][0]["url"]
        except:
            pass

    return dict(user=user, user_image=user_image)

def get_all_posts():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, content FROM posts ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    posts = [{"id": row[0], "username": row[1], "content": row[2]} for row in rows]
    return posts

def insert_post(username, content):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO posts (username, content) VALUES (%s, %s)", (username, content))
    conn.commit()
    cur.close()
    conn.close()

def get_post_by_id(post_id):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, content FROM posts WHERE id = %s", (post_id,))
    post = cur.fetchone()
    cur.close()
    conn.close()
    if post:
        return {"id": post[0], "username": post[1], "content": post[2]}
    return None

def get_comments_by_post(post_id):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, post_id, username, content FROM comments WHERE post_id = %s ORDER BY id DESC", (post_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    comments = [{"id": row[0], "post_id": row[1], "username": row[2], "content": row[3]} for row in rows]
    return comments

def insert_comment(post_id, username, content):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO comments (post_id, username, content) VALUES (%s, %s, %s)",
        (post_id, username, content)
    )
    conn.commit()
    cur.close()
    conn.close()

# to do a post
@app.route("/create_post", methods=["POST"])
def create_post():
    token_info = session.get("token_info")
    if not token_info:
        return redirect(url_for("index"))

    sp = Spotify(auth=token_info["access_token"])
    user = sp.current_user()

    content = request.form.get("content")
    if not content.strip():
        flash("Inlägget får inte vara tomt.")
        return redirect(url_for("profile"))

    db.insert_post(username=user["display_name"], content=content)
    flash("Inlägget publicerat!")
    return redirect(url_for("profile"))


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
    return redirect(url_for("profile"))


@app.route("/profile")
def profile():
    token_info = session.get("token_info")
    if not token_info:
        return redirect(url_for("index"))

    sp = Spotify(auth=token_info["access_token"])

    user = sp.current_user()

    user_image = user["images"][0]["url"] if user["images"] else url_for('static', filename='default_profile.png')

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

    posts = get_all_posts()

    return render_template(
        "profile.html",
        user=user,
        user_image=user_image,
        top_tracks=top_tracks,
        top_artists=top_artists,
        genres=top_genres,
        posts=posts,
    )


@app.route("/posts/<int:post_id>", methods=["GET", "POST"])
def post_detail(post_id):
    post = db.get_post_by_id(post_id)
    if not post:
        return "Inlägg hittades inte", 404

    token_info = session.get("token_info")
    if token_info:
        sp = Spotify(auth=token_info["access_token"])
        user = sp.current_user()
    else:
        user = {"display_name": "Anonym"}

    if request.method == "POST":
        username = user["display_name"]
        content = request.form["content"]
        db.insert_comment(post_id, username, content)
        return redirect(url_for("post_detail", post_id=post_id))

    comments = db.get_comments_by_post(post_id)
    return render_template("post_detail.html", post=post, comments=comments, user=user)


@app.route("/logout")
def logout():
    cache_handler = CacheFileHandler(cache_path=".cache")
    if os.path.exists(".cache"):
        os.remove(".cache")
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
