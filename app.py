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

    if token_info is None:
        return redirect(url_for("index"))

    user_profile_dict = get_user_profile(token_info["access_token"], session["user_id"])

    return render_template(
        "profile.html",
        user=user_profile_dict["user"],
        top_tracks=user_profile_dict["top_tracks"],
        top_artists=user_profile_dict["top_artists"],
        genres=user_profile_dict["top_genres"],
        bio=user_profile_dict["bio"],
        spotify_url=user_profile_dict["spotify_url"],
    )


@app.route("/create_subforum", methods=["POST"])
def create_subforum():
    name = request.form.get("name")
    description = request.form.get("subforum_description")
    creator_id = session.get("user_id")

    if creator_id is None:
        return redirect(url_for("index"))

    is_subforum_created = create_subforum_in_db(name, description, creator_id)
    if is_subforum_created is False:
        return render_template(
            "error.html", error="Subforum med samma namn existerar redan."
        )
    return redirect(url_for("show_subforum", name=name))


@app.route("/create_bio", methods=["POST"])
def create_bio():
    bio = request.form.get("bio")
    song = request.form.get("song")
    creator_id = session.get("user_id")

    if creator_id is None:
        return redirect(url_for("index"))

    update_user_bio(bio, song, creator_id)
    return redirect(url_for("profile"))


@app.route("/subforum/<name>")
def show_subforum(name):
    subforum_data_dict = get_subforum_data(name)
    if subforum_data_dict is None:
        return redirect(url_for("error", error="Subforumet existerar inte."))

    user = get_user(session["token_info"]["access_token"])

    return render_template(
        "subforum.html",
        name=name,
        forum=subforum_data_dict["subforum"],
        threads=subforum_data_dict["threads"],
        user=user,
    )


@app.route("/error")
def error():
    user = get_user(session["token_info"]["access_token"])

    error_message = request.args.get("error")
    return render_template("error.html", error=error_message, user=user)


@app.errorhandler(404)
def page_not_found(err):
    user = get_user(session["token_info"]["access_token"])

    return (
        render_template(
            "error.html", error="Sidan du försöker nå, existerar inte.", user=user
        ),
        404,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
