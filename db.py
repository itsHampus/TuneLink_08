import os

import psycopg2
from psycopg2 import extras

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
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, forum_id , creator_id, title, spotify_url, description, is_pinned, created_at, updated_at
        FROM threads
        WHERE forum_id = %s
        ORDER BY created_at DESC
        """,
        (forum_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    threads = []
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
        }
        threads.append(thread)

    return threads


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
            The ID of the subforum


    Returns
    -------"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO subforum_subscriptions (user_id, forum_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING RETURNING id
            """,
            (user_id, forum_id)
        )
        inserted = cur.fetchone()
        conn.commit()
        return inserted
    finally:
        cur.close()
        conn.close()
        return None

def unsubscribe_from_forum(user_id, forum_id):
    """
    Unsubscribes a user from a subforum

    Args
    -------
        user_id : int
            The ID of the user.
        forum_id : int
            The ID of the subforum


    Returns
    -------
        Inserted
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            DELETE FROM subforum_subscriptions
            WHERE user_id = %s AND forum_id = %s
            RETURNING id
            """,
            (user_id, forum_id)
        )
        deleted = cur.fetchone()
        conn.commit()
        return deleted
    finally:
        cur.close()
        conn.close()
        return None


def search_subforums_by_name(query):
    """
    Searches for subforums by its name

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
            (f"%{query}%",)
        )
        rows = cur.fetchall()
        return [{"id": row[0], "name": row[1], "description": row[2]} for row in rows]
    finally:
        cur.close()
        conn.close()

          

def get_user_subscriptions(user_id):
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
            (user_id,))
        rows = cur.fetchall()
        return [{"id": row[0], "name": row [1]} for row in rows]
    finally:
        cur.close()
        conn.close()

def get_subforum_by_name(name):
    """""fetches a subforum by its name from the database."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, name, description
            FROM forums
            WHERE name = %s
            """, (name,))
        row = cur.fetchone()
        print("DEBUG rows from DB:", row)
        if row is not None:
            return {"id": row[0], "name": row[1]}
        return None
    finally:
        cur.close()
        conn.close()


# function that creates comment
def create_comment(thread_id, user_id, description, spotify_url=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO t_comments (thread_id, user_id, description, spotify_url)
        VALUES (%s, %s, %s, %s)
        """,
        (thread_id, user_id, description, spotify_url)
    )
    conn.commit()
    cur.close()
    conn.close()

def create_thread(forum_id, creator_id, title, spotify_url, description):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO threads (forum_id, creator_id, title, spotify_url, description, is_pinned, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (forum_id, creator_id, title, spotify_url, description)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_subforum_name(subforum_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM forums WHERE id = %s", (subforum_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

def get_all_forums():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM forums")
    forums = [{"id": row[0], "name": row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return forums

def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, bio, spotify_url FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        print("here is what it's returning")
        print({
            "id": user[0],
            "username": user[1],
            "bio": user[2],
            "spotify_url": user[3]
        })
        return {
            "id": user[0],
            "username": user[1],
            "bio": user[2],
            "spotify_url": user[3]
        }
    return None

def get_comments_for_thread(thread_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT t_comments.*, users.username
        FROM t_comments
        JOIN users ON t_comments.user_id = users.id
        WHERE thread_id = %s
        ORDER BY created_at ASC
        """,
        (thread_id,)
    )
    comments = cur.fetchall()
    cur.close()
    conn.close()
    return comments

def get_thread_by_id(thread_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM threads WHERE id = %s", (thread_id,))
    thread = cur.fetchone()
    cur.close()
    conn.close()
    return dict(thread) if thread else None

def get_all_threads():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT threads.id, threads.forum_id, threads.creator_id, threads.title, 
               threads.spotify_url, threads.description, threads.is_pinned, 
               threads.created_at, threads.updated_at, 
               users.username 
        FROM threads 
        JOIN users ON threads.creator_id = users.id
        ORDER BY threads.created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    threads = []
    for row in rows:
        trad = {
            "id": row[0],
            "forum_id": row[1],
            "creator_id": row[2],
            "title": row[3],
            "spotify_url": row[4],
            "description": row[5],
            "is_pinned": row[6],
            "created_at": row[7],
            "updated_at": row[8],
            "creator_name": row[9],
            "image_url": None,
            "last_updated": row[8]
        }
        threads.append(trad)
    return threads

# so that the edit saves
def update_thread(thread_id, title, description):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE threads 
        SET title = %s, description = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (title, description, thread_id))

    conn.commit()
    cur.close()
    conn.close()

def get_forum_name_by_id(forum_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM forums WHERE id = %s", (forum_id,))
        result = cur.fetchone()
        return result[0] if result else None

def db_get_thread_by_id(thread_id):
    return db.fetchone("SELECT * FROM threads WHERE id = %s", (thread_id,))

# function to edit post
def update_post(post_id, new_title, new_description):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE t_threads SET title = %s, description = %s WHERE id = %s",
        (new_title, new_description, post_id)
    )
    conn.commit()
    cur.close()
    conn.close()

# function to edit comment
def update_comment(comment_id, new_description, new_spotify_url=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE t_comments SET description = %s, spotify_url = %s WHERE id = %s",
        (new_description, new_spotify_url, comment_id)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_comment(comment_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM t_comments WHERE id = %s", (comment_id,))
    comment = cur.fetchone()
    cur.close()
    conn.close()
    return comment
