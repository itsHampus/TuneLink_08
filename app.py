import os

from dotenv import load_dotenv

from flask import Flask, redirect, render_template, request, session, url_for, jsonify, flash

from auth import handle_callback, spotify_auth
from db import create_subforum_in_db, get_subforum_data, update_user_bio,search_subforums_by_name,  subscribe_to_forum, unsubscribe_from_forum, get_user_subscriptions,get_user_profile_db,get_subforum_by_name

# setting import on a new line because the one above is too long
from db import create_thread_db

from spotify import get_user, get_user_profile
from spotipy import Spotify

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")


@app.context_processor
def user_injection():
    """Injects the user into the template context.

    """
    user = None
    subscribed_forums = []
    subscribed_forum_ids = []

    token_info = session.get("token_info")
    user_id = session.get("user_id")
    print(f"DEBUG user_id from session: {user_id}")

    token_info = session.get("token_info")
    if token_info is not None:
        try:
            sp = Spotify(auth=token_info["access_token"])
            user = sp.current_user()
            if user_id is not None:
                subscribed_forums = get_user_subscriptions(user_id)
                subscribed_forum_ids = [forum["id"] for forum in subscribed_forums]

        except Exception as e:
            print(f"Fel vid hämtning av användarinfo: {e}")
    return dict(user=user,
                subscribed_forums=subscribed_forums,
                subscribed_forum_ids=subscribed_forum_ids,)

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

@app.route("/subscribe/<string:name>", methods=["POST"])
def subscribe(name):
    subforum = get_subforum_by_name(name)
    if subforum is None:
        return redirect(url_for("error", error="Subforumet existerar inte."))

    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("index"))

    success = subscribe_to_forum(user_id, subforum["id"])
    if success is True:
        flash("Du har nu prenumererat på subforumet!")
    else:
        flash("Du prenumererar redan på subforumet!")
    return redirect(url_for("show_subforum", name = subforum["name"]))

@app.route("/unsubscribe/<string:name>", methods=["POST"])
def unsubscribe(name):
    """
    Unsubscribes the user from a subforum.
    Args"""
    subforum = get_subforum_by_name(name)
    if subforum is None:
        return redirect(url_for("error", error="subforumet existerar inte."))

    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("index"))

    success = unsubscribe_from_forum(user_id, subforum["id"])
    if success is True:
        flash("Du har avprenumererat från subforumet!")
    else:
        flash("Du prenumererar inte på subforumet!")
    return redirect(url_for("show_subforum", name = subforum["name"]))


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


@app.route("/subforum/<name>/create_thread_route", methods=["POST"])
def create_thread_app(name):

    """ function that creates a thread, function name ends with _app to avoid confusion with the function in db.py
        it gets the values from the modal in subforum.html

        Args
        -------
            name : string
                name of the subforum

        Returns
        -------

        """

    forum = get_subforum_by_name(name)
    if forum is None:
        return redirect(url_for("error"))

    title = request.form.get("title")

    # if title is None or empty string it will cause problems
    if title == None or "":
        title = "title placeholder"

    spotify_url = request.form.get("spotify_url")

    # if invalid spotify url is entered the form will give None or empty string and cause problems
    # so i'm setting it as "placeholder" string instead
    
    if spotify_url == None or "":
        spotify_url = "spotify_url placeholder"

    description = request.form.get("description")

    # if description is None or empty string it will also cause problems
    if description == None or "":
        description = "description placeholder"

    creator_id = session.get("user_id")

    # changing it to checking if creator_id is not int type because otherwise it will cause problems
    if type(creator_id) != int:
        return redirect(url_for("index"))

    create_thread_db(forum["id"], creator_id, title, spotify_url, description)

    return redirect(url_for("show_subforum", name=name))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/ajax/search_subforums")
def ajax_search_subforums():
    query = request.args.get("q", "").strip()
    if query is None:
        return jsonify([])

    results = search_subforums_by_name(query)
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)
