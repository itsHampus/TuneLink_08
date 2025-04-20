import os
import db
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for
from spotipy import Spotify
from spotipy.cache_handler import CacheFileHandler, FlaskSessionCacheHandler
from spotipy.oauth2 import SpotifyOAuth

from db import get_connection, get_forum_by_name, get_threads_by_forum

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

    cur.execute("SELECT id FROM users WHERE spotify_id = %s", (spotify_id,))
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO users(spotify_id, username) VALUES (%s,%s) RETURNING id;",
            (spotify_id, display_name),
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

    user_image = user["images"][0]["url"] if user.get("images") else url_for("static", filename="default_profile.png")

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

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT bio, spotify_url FROM users WHERE id = %s", (session["user_id"],)
    )
    results = cur.fetchone()
    cur.close()
    conn.close()

    bio = results[0] if results else ""

    spotify_url = results[1] if results else ""

    user_id = session["user_id"]
    user = db.get_user_by_id(user_id)
    top_artists = session.get("top_artists", [])
    top_tracks = session.get("top_tracks", [])
    top_genres = session.get("top_genres", [])

    # getting what's required to create post and comment
    forums = db.get_all_forums()
    threads = db.get_all_threads()

    return render_template(
        "profile.html",
        user=user,
        user_image=user_image,
        top_tracks=top_tracks,
        top_artists=top_artists,
        genres=top_genres,
        bio=bio,
        spotify_url=spotify_url,
        forums=forums,
        threads=threads
    )


@app.route("/create_subforum", methods=["POST"])
def create_subforum():
    print(request.form)
    name = request.form.get("name")
    description = request.form.get("thread_description")
    creator_id = session.get("user_id")

    if not creator_id:
        return redirect(url_for("index"))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM forums WHERE name = %s", (name,))
    if cur.fetchone():
        print("Forum with that name already exists!!!!")
        cur.close()
        conn.close()
        return redirect(url_for("profile"))

    cur.execute(
        "INSERT INTO forums(name, description, creator_id) VALUES (%s, %s, %s)",
        (name, description, creator_id),
    )

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("show_subforum", name=name))


@app.route("/create_bio", methods=["POST"])
def create_bio():
    bio = request.form.get("bio")
    song = request.form.get("song")
    creator_id = session.get("user_id")

    if not creator_id:
        return redirect(url_for("index"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET bio = %s, spotify_url = %s WHERE id = %s",
        (bio, song, creator_id),
    )

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("profile", song=song, bio=bio))


@app.route("/subforum/<name>")
def show_subforum(name):
    forum = get_forum_by_name(name)
    if forum is None:
        return redirect(url_for("profile"))

    threads = get_threads_by_forum(forum_id=forum["id"])

    token_info = session.get("token_info")
    if not token_info:
        return redirect(url_for("index"))
    sp = Spotify(auth=token_info["access_token"])
    user = sp.current_user()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM forums ORDER BY name")
    subforums = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "subforum.html",
        name=name,
        forum=forum,
        threads=threads,
        user=user,
        subforums=subforums
    )

@app.route("/logout")
def logout():
    cache_handler = CacheFileHandler(cache_path=".cache")
    if os.path.exists(".cache"):
        os.remove(".cache")
    session.clear()
    return redirect(url_for("index"))

# function that creates post in selected subforum
@app.route("/subforum/<int:subforum_id>/create_post", methods=["POST"])
def create_subforum_post(subforum_id):
    if "token_info" not in session:
        return redirect(url_for("index"))

    user = get_current_user()
    content = request.form.get("content")

    if content:
        db.create_comment(subforum_id, user["id"], content)

    return redirect(url_for("show_subforum", name=db.get_subforum_name(subforum_id)))

@app.route("/create_post/<int:thread_id>", methods=["POST"])
def create_post(thread_id):
    user = get_current_user()
    if not user:
        return redirect(url_for("index"))

    content = request.form["content"]
    db.create_comment(thread_id, user["id"], content)
    return redirect(url_for("view_thread", thread_id=thread_id))



@app.route("/create_thread", methods=["POST"])
def create_thread():
    forum_id = request.form.get("forum_id")
    title = request.form.get("title")
    spotify_url = request.form.get("spotify_url")
    description = request.form.get("description")

    if forum_id and title:
        db.create_thread(
            forum_id=forum_id,
            creator_id=session["user_id"],
            title=title,
            spotify_url=spotify_url,
            description=description
        )
        forum_name = db.get_subforum_name(forum_id)
        return redirect(url_for("show_subforum", name=forum_name))
    else:
        flash("Titel och subforum är obligatoriska.", "danger")
        return redirect(url_for("profile"))

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.get_user_by_id(user_id)

@app.route("/thread/<int:thread_id>", methods=["GET", "POST"])
def view_thread(thread_id):
    thread = db.get_thread_by_id(thread_id)
    if not thread:
        return redirect(url_for("profile"))

    comments = db.get_comments_for_thread(thread_id)

    token_info = session.get("token_info")
    if not token_info:
        return redirect(url_for("index"))
    sp = Spotify(auth=token_info["access_token"])
    user = sp.current_user()

    if request.method == "POST":
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("index"))
        description = request.form.get("description")
        spotify_url = request.form.get("spotify_url") or None
        db.add_comment(thread_id, user_id, description, spotify_url)
        return redirect(url_for("view_thread", thread_id=thread_id))

    return render_template("thread.html", thread=thread, comments=comments, user=user)

@app.route("/comment_from_profile", methods=["POST"])
def comment_from_profile():
    thread_id = request.form.get("thread_id")
    content = request.form.get("content")
    user_id = session.get("user_id")

    if not thread_id or not content or not user_id:
        return redirect(url_for("profile"))

    db.create_comment(thread_id, user_id, content)
    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True)
