import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for

from auth import handle_callback, spotify_auth
from db import create_subforum_in_db, get_subforum_data, update_user_bio, get_connection, get_all_forums, create_thread_in_db, get_forum_name_by_id
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

# create thread button
@app.route('/create_thread', methods=['GET', 'POST'])
def select_forum_to_create_thread():
    if request.method == 'POST':
        forum_id = request.form.get('forum_id')
        if not forum_id:
            return render_template("error.html", error="Inget subforum valt.")
        return redirect(url_for("create_thread", forum_id=forum_id))

    forums = get_all_forums()
    user = get_user(session["token_info"]["access_token"])
    return render_template('select_forum.html', forums=forums, user=user)

# formulär för att skapa tråd
@app.route('/create_thread/<int:forum_id>', methods=['GET', 'POST'])
def create_thread(forum_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("index"))

    if request.method == 'POST':
        title = request.form.get("title")
        spotify_url = request.form.get("spotify_url")
        description = request.form.get("description")

        success = create_thread_in_db(forum_id, user_id, title, spotify_url, description)
        if success:
            forum_name = get_forum_name_by_id(forum_id)
            return redirect(url_for("show_subforum", name=forum_name))
        else:
            return render_template("error.html", error="Kunde inte skapa tråd.")

    user = get_user(session["token_info"]["access_token"])
    return render_template("create_thread.html", forum_id=forum_id, user=user)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/thread/<int:thread_id>/comment", methods=["GET", "POST"])
def create_comment(thread_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "POST":
        description = request.form["description"]
        spotify_url = request.form.get("spotify_url")
        user_id = session["user_id"]

        db.execute(
            "INSERT INTO t_comments (thread_id, user_id, description, spotify_url) VALUES (%s, %s, %s, %s)",
            (thread_id, user_id, description, spotify_url)
        )
        return redirect(url_for("show_thread", thread_id=thread_id))

    thread = db.fetchone("SELECT * FROM threads WHERE id = %s", (thread_id,))
    return render_template("create_comment.html", thread=thread)

# to create a thread
@app.route('/forum/<int:forum_id>/create_thread', methods=['POST'])
def create_thread_from_subforum(forum_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    title = request.form.get('title')
    spotify_url = request.form.get('spotify_url')
    description = request.form.get('description')
    user_id = session['user_id']

    db.create_thread(title=title, spotify_url=spotify_url, description=description, user_id=user_id, forum_id=forum_id)

    return redirect(url_for('forum_view', forum_id=forum_id))


@app.route("/thread/<int:thread_id>")
def show_thread(thread_id):
    from db import get_thread_by_id, get_comments_by_thread

    thread = get_thread_by_id(thread_id)
    if not thread:
        return render_template("error.html", error="Tråden kunde inte hittas.")

    comments = get_comments_by_thread(thread_id)
    user = get_user(session["token_info"]["access_token"])

    return render_template("thread.html", thread=thread, comments=comments, user=user)

# to get the threads on an arbitrary page
@app.route('/all_threads')
def all_threads():
    threads = db.get_all_threads()
    return render_template('all_threads.html', threads=threads)


if __name__ == "__main__":
    app.run(debug=True)
