import os

import psycopg2


def get_connection():
    """Establishes a connection to the PostgreSQL database.

    Returns
    -------
        psycopg2.connect
            A connection object to the PostgreSQL database.

    """
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_USER_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


def get_subforum_by_name(name):
    """Fetches a subforum by its name from the database.

    Args
    -------
        name : str
            The name of the subforum.

    Returns
    -------
        dict
            A dictionary containing the subforum's ID, name and description
        None
            If the subforum does not exist.

    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, description FROM forums WHERE name = %s", (name,))
    forum = cur.fetchone()
    cur.close()
    conn.close()

    if forum is not None:
        forum_id, forum_name, *optional_description = forum

        description = optional_description[0] if len(optional_description) > 0 else None

        return {"id": forum_id, "name": forum_name, "description": description}
    else:
        return None


def get_threads_by_name(name):
    """Fetches a thread by its name from the database.

    Args
    -------
        name : str
            The name of the thread.

    Returns
    -------
        dict
            A dictionary containing the thread's ID, name and description
        None
            If the thread does not exist.
    """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, description FROM forums WHERE name = %s", (name,))
    forum = cur.fetchone()
    cur.close()
    conn.close()
    if forum is not None:
        return {"id": forum[0], "name": forum[1], "description": forum[2]}
    else:
        return None


def create_thread_in_db(forum_id, creator_id, title, spotify_url, description):
    """Function that creates a thread and inserts it into the database table "threads". Function name ends with _db to avoid confusion with the function in app.py.

    Args
    -------
        forum_id : int
            ID of the forum.
        creator_id : int
            ID of the user creating the thread.
        title : str
            Title of the thread.
        spotify_url : str
            Spotify URL of the thread.
        description : str
            Description to the thread.
    Returns
    -------
        None
    """

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO threads (
                forum_id,
                creator_id,
                title,
                spotify_url,
                description
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (forum_id, creator_id, title, spotify_url, description),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        conn.rollback()
        print("Error trying to create thread in db at create_thread_db: " + str(e))
    finally:
        cur.close()
        conn.close()


def get_all_threads():
    """Retrives the 15 most recent threads from the database.

    The threads are ordered by their creation date in descending order.

    Returns
    -------
        list of dict
            A list of dictionaries, each containing the thread's ID, title, description,
            Spotify URL, creation date, and the username of the creator.
        Returns an empty list if no threads are found or an error occurs.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                threads.id,
                threads.title,
                threads.description,
                threads.spotify_url,
                threads.created_at,
                users.username
            FROM threads
            JOIN users ON threads.creator_id = users.id
            ORDER BY threads.created_at DESC
            LIMIT 15
            """
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "spotify_url": row[3],
                "created_at": row[4],
                "username": row[5],
            }
            for row in rows
        ]
    except Exception as e:
        return []
    finally:
        cur.close()
        conn.close()


def get_threads_by_forum(forum_id):
    """Fetches all threads associated with a specific forum based on the forum ID.

    Args
    -------
        forum_id : int
            The ID of the forum.
    Returns
    -------
        list
            A list of dictionaries, each containing the thread's information.
    """
    conn = get_connection()

    threads = []
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                threads.id,
                threads.forum_id,
                threads.creator_id,
                threads.title,
                threads.spotify_url,
                threads.description,
                threads.is_pinned,
                threads.created_at,
                threads.updated_at,
                users.username
            FROM threads
            JOIN users ON threads.creator_id = users.id
            WHERE threads.forum_id = %s
            ORDER BY threads.created_at DESC
            """,
            (forum_id,),
        )
        rows = cur.fetchall()

        for row in rows:
            thread = {
                "id": row[0],
                "forum_id": row[1],
                "creator_id": row[2],
                "title": row[3],
                "spotify_url": row[4],
                "description": row[5],
                "is_pinned": row[6],
                "created_at": row[7],
                "updated_at": row[8],
                "username": row[9],
            }
            threads.append(thread)

        return threads
    except Exception as e:
        conn.rollback()
        print(f"Error fetching threads in get_threads_by_forum: {e}")
        return []
    finally:
        conn.close()
        cur.close()


def get_user_profile_db(user_id):
    """Fetches the user profile from the database based on the user ID.

    Args
    -------
        user_id : int
            The ID of the user.

    Returns
    -------
        dict
            A dictionary containing the user's bio and Spotify URL.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT bio, spotify_url FROM users WHERE id = %s", (user_id,))
    results = cur.fetchone()
    cur.close()
    conn.close()

    bio = results[0] if len(results) > 0 else ""
    spotify_url = results[1] if len(results) > 0 else ""

    return {"bio": bio, "spotify_url": spotify_url}


def controll_user_login(spotify_id, display_name):
    """Checks if a user exists in the database and creates a new user if not.

    Args
    -------
        spotify_id : str
            The Spotify ID of the user.
        display_name : str
            The display name of the user.

    Returns
    -------
        user_id : int
            The ID of the user in the database.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE spotify_id = %s", (spotify_id,))
    user_id = cur.fetchone()

    if len(user_id) == 0:
        cur.execute(
            "INSERT INTO users(spotify_id, username) VALUES (%s, %s) RETURNING id;",
            (spotify_id, display_name),
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return user_id
    else:
        cur.close()
        conn.close()
        return user_id[0]


def create_subforum_in_db(name, description, creator_id):
    """Creates a new subforum in the database.

    Args
    -------
        name : str
            The name of the subforum.
        description : str
            The description of the subforum.
        creator_id : int
            The ID of the user creating the subforum.

    Returns
    -------
        bool
            True if the subforum was created successfully, False if it already exists.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM forums WHERE name = %s", (name,))

        if cur.fetchone():
            return False
        cur.execute(
            "INSERT INTO forums(name, description, creator_id) VALUES (%s, %s, %s)",
            (name, description, creator_id),
        )
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()


def update_user_bio(bio, song, creator_id):
    """Updates the user's bio and Spotify URL in the database.

    Args
    -------
        bio : str
            The bio of the user.
        song : str
            The Spotify URL of the user's song.
        creator_id : int
            The ID of the user.

    Returns
    -------
        None
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET bio = %s, spotify_url = %s WHERE id = %s",
        (bio, song, creator_id),
    )
    conn.commit()

    cur.close()
    conn.close()


def get_subforum_data(name):
    """Fetches subforum data by the subforum name.

    Args
    -------
        name : str
            The name of the subforum.

    Returns
    -------
        dict
            A dictionary containing the subforum and its associated threads.
        None
            If the subforum does not exist.
    """
    subforum_dict = get_subforum_by_name(name)

    if subforum_dict is None:
        return None

    threads = get_threads_by_forum(subforum_dict["id"])

    return {"subforum": subforum_dict, "threads": threads}


def subscribe_to_forum(user_id, forum_id):
    """Subscribes a user to a subforum

    Args
    -------
        user_id : int
            The ID of the user.
        forum_id : int
            The ID of the subforum.


    Returns
    -------
        bool
            True if the subscription was successful,
            False if the user was already subscribed or an error occurred.

    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO subforum_subscriptions (user_id, forum_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (user_id, forum_id),
        )
        conn.commit()

        if cur.rowcount > 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error subscribing to forum: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def unsubscribe_from_forum(user_id, forum_id):
    """Unsubscribes a user from a subforum

    Args
    -------
        user_id : int
            The ID of the user.
        forum_id : int
            The ID of the subforum


    Returns
    -------
        bools
            True if the user was successfully subscribed
            False if the user was already subscribed
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            DELETE FROM subforum_subscriptions
            WHERE user_id = %s AND forum_id = %s
            """,
            (user_id, forum_id),
        )
        conn.commit()
        if cur.rowcount > 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error unsubscribing from forum: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def search_subforums_by_name(query):
    """Searches for subforums by its name

    Args
    ------
        query : str
            The name of the subforum.

    Returns
    -------
        list : [dict]
            A list of dictionaries containing the subforum names.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, name, description
            FROM forums
            WHERE LOWER (name) LIKE LOWER (%s)
            ORDER BY name ASC
            LIMIT 10
            """,
            (f"%{query}%",),
        )
        rows = cur.fetchall()
        return [{"id": row[0], "name": row[1], "description": row[2]} for row in rows]
    finally:
        cur.close()
        conn.close()


def get_user_subforum_subscriptions(user_id):
    """Fetches all subforums the user is subscribed to.

    Args
    -------
        user_id : int
            The ID of the user to fetch subscriptions for.


    Returns
    -------
        list of dict
            A list of dictionaries containing the subforum's id (int) and name (str)

    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT forums.id, forums.name
            FROM forums
            JOIN subforum_subscriptions ON forums.id = subforum_subscriptions.forum_id
            WHERE subforum_subscriptions.user_id = %s
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        return [{"id": row[0], "name": row[1]} for row in rows]
    except Exception as e:
        print(f"Error fetching user subforum subscriptions: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_subforum_by_name(name):
    """Fetches a subforum by its name from the database.


    Args
    -------
        name : str
            The name of the subforum to be fetched.


    Returns
    -------
        dict
            a dictionary containing the subforum's id(int) and name (str)

        None
            if no subforum with the given name exists.

    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, name, description
            FROM forums
            WHERE name = %s
            """,
            (name,),
        )
        row = cur.fetchone()

        if row is not None:
            return {"id": row[0], "name": row[1]}
        return None
    finally:
        cur.close()
        conn.close()


def get_thread_by_id(thread_id):
    """Fetches a thread by its id from the DB

    Args
    -------
        thread_id : int
            The id of the thread.

    Returns
    -------
        dict
            A dict containing the threads id, name and description

        None
            If the thread does not exist.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                threads.id,
                threads.title,
                threads.description,
                threads.spotify_url,
                threads.created_at,
                users.username,
                forums.name as subforum_name
            FROM threads
            JOIN users ON threads.creator_id = users.id
            JOIN forums ON threads.forum_id = forums.id
            WHERE threads.id = %s
            """,
            (thread_id,),
        )
        row = cur.fetchone()
        if row is not None:
            return {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "spotify_url": row[3],
                "created_at": row[4],
                "username": row[5],
                "subforum_name": row[6],
            }
        return None
    except Exception as e:
        print(f"Error fetching thread by id: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def register_thread_like_or_dislike(user_id, thread_id, vote):
    """Registers, updates or removes a like or dislike for a thread by a user.

    If the user clicks the same vote (like or dislike) twice, the vote is removed.
    If the user changes their vote, the new vote is registered.

    Args
    -----
        user_id : int
            The ID of the user.
        thread_id : int
            The ID of the thread.
        vote : int
            The vote value, 1 for like and -1 for dislike.

    Returns
    -----
        None
    """
    conn = get_connection()
    cur = conn.cursor()
    try:

        cur.execute(
            "DELETE FROM likes WHERE user_id = %s AND thread_id = %s AND vote = %s",
            (user_id, thread_id, vote),
        )
        if cur.rowcount == 0:
            cur.execute(
                """
                INSERT INTO likes (user_id, thread_id, vote)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, thread_id)
                DO UPDATE SET vote = EXCLUDED.vote
                """,
                (user_id, thread_id, vote),
            )
        conn.commit()
    except Exception as e:
        print(f"Error registering thread like/dislike: {e}")
    finally:
        cur.close()
        conn.close()


def get_thread_likes_and_dislikes(thread_id):
    """Retrieves the total number of likes and dislikes for a specific thread.

    Args
    -----
        thread_id : int
            The ID of the thread.

    Returns
    -----
        dict
            A dictionary containing the total likes and dislikes for the thread.
            Example: {"likes": 10, "dislikes": 2}

        If an error occurs, returns {"likes": 0, "dislikes": 0}.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                SUM(CASE WHEN vote = 1 THEN 1 ELSE 0 END) AS likes,
                SUM(CASE WHEN vote = -1 THEN 1 ELSE 0 END) AS dislikes
            FROM likes
            WHERE thread_id = %s
            """,
            (thread_id,),
        )
        row = cur.fetchone()
        return {"likes": row[0] or 0, "dislikes": row[1] or 0}
    except Exception as e:
        print(f"Error fetching thread likes and dislikes: {e}")
        return {"likes": 0, "dislikes": 0}
    finally:
        cur.close()
        conn.close()


def get_comments_for_thread(thread_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                t_comments.description,
                t_comments.created_at,
                users.username,
                t_comments.spotify_url
            FROM t_comments
            JOIN users ON t_comments.user_id = users.id
            WHERE t_comments.thread_id = %s
            ORDER BY t_comments.created_at ASC
            """,
            (thread_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "description": row[0],
                "created_at": row[1],
                "username": row[2],
                "spotify_url": row[3]
            }
            for row in rows
        ]
    except Exception as e:
        print(f"Error fetching comments for thread {thread_id}: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def delete_subforum_from_db(name, user_id):
    """
    Deletes a subforum from the database if the user is an admin.

    Args
    ------
        name : str
            The name of the subforum to delete.
        user_id : int
            The ID of the user attempting to delete the subforum.

    Returns
    -------
        bool
            True if the subforum was deleted, False otherwise.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    if not result or result[0] != "admin":
        cur.close()
        conn.close()
        return False

    cur.execute("DELETE FROM forums WHERE name = %s", (name,))
    conn.commit()
    cur.close()
    conn.close()
    return True


def get_user_role(user_id):
    """
    Fetches the role of a user from the database.

    Args
    ------
        user_id : int
            The ID of the user.

    Returns
    -------
        str
            The role of the user, or None if not found.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None


def add_comment_to_thread(thread_id, user_id, description, spotify_url=None):
   conn = get_connection()
   cur = conn.cursor()
   cur.execute("""
       INSERT INTO t_comments (thread_id, user_id, description, spotify_url)
       VALUES (%s, %s, %s, %s)
   """, (thread_id, user_id, description, spotify_url))
   conn.commit()
   cur.close()
   conn.close()


def get_threads_by_user_subscriptions(user_id):
    """Retrives all threads the user is subscribed to.

    Args
    ------
        user_id : int
            The ID of the user in the database

    Returns
    -------
        list of dict
            A list of dictionaries with the following key
            - id : int
            - title : str
            - description : str
            - spotify_url : str
            -created_at : datetime
            - username : str

        Returns an empty list if no threads are found or an error occurs.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                threads.id,
                threads.title,
                threads.description,
                threads.spotify_url,
                threads.created_at,
                users.username
            FROM threads
            JOIN users ON threads.creator_id = users.id
            JOIN subforum_subscriptions ss ON ss.forum_id = threads.forum_id
            WHERE ss.user_id = %s
            ORDER BY threads.created_at DESC
            """,
            (user_id,),
        )
        subscriptions = cur.fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "spotify_url": row[3],
                "created_at": row[4],
                "username": row[5],
            }
            for row in subscriptions
        ]
    except Exception as e:
        print(f"Error fetching threads by user subscriptions: {e}")
        return []
    finally:
        cur.close()
        conn.close()
