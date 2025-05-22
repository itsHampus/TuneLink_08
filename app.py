import os

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from spotipy import Spotify

import db
from auth import handle_callback, spotify_auth

import db

from spotify import get_user, get_user_profile, get_album_image_url,get_dashboard_data
from spotipy import Spotify


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")


@app.context_processor
def user_injection():
    """Injects the user into the template context."""
    user = None
    subscribed_forums = []
    subscribed_forum_ids = []
    role = None
    token_info = session.get("token_info")
    user_id = session.get("user_id")
    

    if token_info is not None:
        try:
            sp = Spotify(auth=token_info["access_token"])
            user = sp.current_user()
            if user_id is not None:
                subscribed_forums = db.get_user_subscriptions(user_id)
                subscribed_forum_ids = [forum["id"] for forum in subscribed_forums]

                role = db.get_user_role(user_id)

        except Exception as e:
            print(f"Fel vid hämtning av användarinfo: {e}")

    return dict(user=user,
                subscribed_forums=subscribed_forums,
                subscribed_forum_ids=subscribed_forum_ids,
                role=role,)

    return dict(
        user=user,
        subscribed_forums=subscribed_forums,
        subscribed_forum_ids=subscribed_forum_ids,
    )



@app.route("/")
def index():
    auth_url = spotify_auth(session)
    return render_template("index.html", auth_url=auth_url)


@app.route("/callback")
def callback():
    handle_callback(session)
    return redirect(url_for("profile"))

@app.route("/dashboard")
def dashboard(user_id,token_info):

    if token_info is None or user_id is None:
        return redirect(url_for("index"))

    user, threads = get_dashboard_data(token_info, user_id)

    return render_template("dashboard.html",
                            threads=threads,
                            user=user)


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

    is_subforum_created = db.create_subforum_in_db(name, description, creator_id)
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

    db.update_user_bio(bio, song, creator_id)
    return redirect(url_for("profile"))


@app.route("/subforum/<name>")
def show_subforum(name):
    subforum_data_dict = db.get_subforum_data(name)
    if subforum_data_dict is None:
        return redirect(url_for("error", error="Subforumet existerar inte."))

    token_info = session.get("token_info")
    if token_info is None:
        return redirect(url_for("index"))

    sp = Spotify(auth=token_info["access_token"])
    user = get_user(session["token_info"]["access_token"])

    threads = subforum_data_dict["threads"]
    for thread in threads:
        thread["image_url"] = get_album_image_url(thread["spotify_url"], sp)

    return render_template(
        "subforum.html",
        name=name,
        forum=subforum_data_dict["subforum"],
        threads=threads,
        user=user,
    )


@app.route("/subscribe/<string:name>", methods=["POST"])
def subscribe(name):
    subforum = db.get_subforum_by_name(name)
    if subforum is None:
        return redirect(url_for("error", error="Subforumet existerar inte."))

    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("index"))

    success = db.subscribe_to_forum(user_id, subforum["id"])

    if success is True:
        flash("Du har nu prenumererat på subforumet!")

    else:
        flash("Du prenumererar redan på subforumet!")
    return redirect(url_for("show_subforum", name=subforum["name"]))


@app.route("/unsubscribe/<string:name>", methods=["POST"])
def unsubscribe(name):

    """
    Unsubscribes the user from a subforum.
    Args"""

    subforum = db.get_subforum_by_name(name)
    if subforum is None:
        return redirect(url_for("error", error="subforumet existerar inte."))

    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("index"))

    success = db.unsubscribe_from_forum(user_id, subforum["id"])

    if len(success) > 0:

        flash("Du har avprenumererat från subforumet!")
    else:
        flash("Du prenumererar inte på subforumet!")
    return redirect(url_for("show_subforum", name=subforum["name"]))

@app.route("/thread/<int:thread_id>")
def show_thread(thread_id):
    thread = db.get_thread_by_id(thread_id)
    if thread is None:
        return redirect(url_for("error", error="Tråden existerar inte."))

    token_info = session.get("token_info")
    if token_info is None:
        return redirect(url_for("index"))

    sp = Spotify(auth=token_info["access_token"])
    thread["image_url"] = get_album_image_url(thread["spotify_url"], sp)

    comments = db.get_comments_for_thread(thread_id)
    return render_template("thread.html",
                        thread=thread,
                        comments=comments)

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




@app.route("/delete_subforum/<name>", methods=["POST"])
def delete_subforum(name):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("index"))

    success = db.delete_subforum_from_db(name, user_id)
    if not success:
        flash("Du har inte rättigheter att ta bort detta subforum.")
    else:
        flash("Subforumet har tagits bort.")
    return redirect(url_for("profile"))

    



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/ajax/search_subforums")
def ajax_search_subforums():
    query = request.args.get("q", "").strip()
    if query is None:
        return jsonify([])

    results = db.search_subforums_by_name(query)
    return jsonify(results)



if __name__ == "__main__":
    app.run(debug=True)
