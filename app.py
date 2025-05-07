import os

from dotenv import load_dotenv

from flask import Flask, redirect, render_template, request, session, url_for, jsonify, flash

from auth import handle_callback, spotify_auth
import db
from db import create_subforum_in_db, get_subforum_data, update_user_bio,search_subforums_by_name,  subscribe_to_forum, unsubscribe_from_forum, get_user_subscriptions,get_user_profile_db,get_subforum_by_name, get_all_forums, get_forum_name_by_id, create_thread, get_thread_by_id, get_comments_for_thread
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


# create thread button
@app.route('/create_thread', methods=['GET'])
def show_forum_selection():
    forums = get_all_forums()
    user = get_user(session["token_info"]["access_token"])
    return render_template('select_forum.html', forums=forums, user=user)


@app.route('/create_thread', methods=['POST'])
def handle_forum_selection():
    forum_id = request.form.get('forum_id')
    if not forum_id:
        return render_template("error.html", error="Inget subforum valt.")
    return redirect(url_for("create_thread", forum_id=forum_id))

# formulär för att skapa tråd
@app.route("/create_thread/<int:forum_id>", methods=["GET"])
def show_create_thread_form(forum_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("index"))

    subforum_data_dict = get_subforum_data(get_forum_name_by_id(forum_id))
    if subforum_data_dict is None:
        return render_template("error.html", error="Subforumet existerar inte.")

    user = get_user(session["token_info"]["access_token"])

    return render_template(
        "subforum.html",
        forum=subforum_data_dict["subforum"],
        threads=subforum_data_dict["threads"],
        user=user,
    )


@app.route("/create_thread/<int:forum_id>", methods=["POST"])
def submit_create_thread(forum_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("index"))

    title = request.form.get("title")
    spotify_url = request.form.get("spotify_url")
    description = request.form.get("description")

    success = create_thread_in_db(forum_id, user_id, title, spotify_url, description)
    if success:
        forum_name = get_forum_name_by_id(forum_id)
        return redirect(url_for("show_subforum", name=forum_name))
    else:
        return render_template("error.html", error="Kunde inte skapa tråd.")

@app.route("/thread/<int:thread_id>/comment", methods=["GET"])
def show_comment_form(thread_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    thread = db.db_get_thread_by_id(thread_id)
    return render_template("create_comment.html", thread=thread)


@app.route("/thread/<int:thread_id>/comment", methods=["POST"])
def submit_comment(thread_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    description = request.form["description"]
    spotify_url = request.form.get("spotify_url")
    user_id = session["user_id"]

    db_create_comment(thread_id, user_id, description, spotify_url)
    return redirect(url_for("show_thread", thread_id=thread_id))

# to create a thread
@app.route('/forum/<int:forum_id>/create_thread', methods=['POST'])
def create_thread_from_subforum(forum_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    title = request.form.get('title')
    spotify_url = request.form.get('spotify_url')
    description = request.form.get('description')
    user_id = session['user_id']

    db.create_thread(title=title, spotify_url=spotify_url, description=description, creator_id=user_id, forum_id=forum_id)

    forum_name = get_forum_name_by_id(forum_id)
    return redirect(url_for('show_subforum', name=forum_name))



@app.route("/thread/<int:thread_id>")
def show_thread(thread_id):

    thread = get_thread_by_id(thread_id)
    if not thread:
        return render_template("error.html", error="Tråden kunde inte hittas.")

    comments = get_comments_for_thread(thread_id)
    user = get_user(session["token_info"]["access_token"])

    return render_template("thread.html", thread=thread, comments=comments, user=user)

# to get the threads on an arbitrary page
@app.route('/all_threads')
def all_threads():
    threads = db.get_all_threads()
    return render_template('all_threads.html', threads=threads)


if __name__ == "__main__":
    app.run(debug=True)
