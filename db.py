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
    if not result or result[0] != 'admin' :
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



