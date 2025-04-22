import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for

from auth import handle_callback, spotify_auth
from db import create_subforum_in_db, get_subforum_data, update_user_bio
from spotify import get_user, get_user_profile

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")


@app.route("/")
def index():
    auth_url = spotify_auth(session)
    return render_template("index.html", auth_url=auth_url)


@app.route("/callback")
def callback():
    handle_callback(session)
    return redirect(url_for("profile"))


@app.route("/profile")
def profile():
    token_info = session.get("token_info")
    if not token_info:
        return redirect(url_for("index"))

    user, top_tracks, top_artists, top_genres, bio, spotify_url = get_user_profile(
        session
    )

    return render_template(
        "profile.html",
        user=user,
        top_tracks=top_tracks,
        top_artists=top_artists,
        genres=top_genres,
        bio=bio,
        spotify_url=spotify_url,
    )


@app.route("/create_subforum", methods=["POST"])
def create_subforum():
    name = request.form.get("name")
    description = request.form.get("thread_description")
    creator_id = session.get("user_id")

    if not creator_id:
        return redirect(url_for("index"))

    is_subforum_created = create_subforum_in_db(name, description, creator_id)
    if not is_subforum_created:
        return render_template(
            "error.html", error="Subforum with that name already exists."
        )
    return redirect(url_for("show_subforum", name=name))


@app.route("/create_bio", methods=["POST"])
def create_bio():
    bio = request.form.get("bio")
    song = request.form.get("song")
    creator_id = session.get("user_id")

    if not creator_id:
        return redirect(url_for("index"))

    update_user_bio(bio, song, creator_id)
    return redirect(url_for("profile"))


@app.route("/subforum/<name>")
def show_subforum(name):
    subforum, threads = get_subforum_data(name, session)
    if not subforum:
        return render_template("error.html", error="Subforum not found.")
    user = get_user()
    return render_template(
        "subforum.html", name=name, forum=subforum, threads=threads, user=user
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
