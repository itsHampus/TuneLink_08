import os

import psycopg2


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_USER_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


def get_subforum_by_name(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id , name description FROM forums WHERE name = %s", (name,))
    forum = cur.fetchone()
    cur.close()
    conn.close()

    if forum:
        forum_id, forum_name, *optional_description = forum
        description = optional_description[0] if optional_description else None
        return {"id": forum_id, "name": forum_name, "description": description}
    else:
        return None


def get_threads_by_name(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id , name description FROM forums WHERE name = %s", (name,))
    forum = cur.fetchone()
    cur.close()
    conn.close()
    if forum:
        return {"id": forum[0], "name": forum[1], "description": forum[2]}
    else:
        return None


def get_threads_by_forum(forum_id):
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT bio, spotify_url FROM users WHERE id = %s", (user_id,))
    results = cur.fetchone()
    cur.close()
    conn.close()

    bio = results[0] if results else ""
    spotify_url = results[1] if results else ""
    return {"bio": bio, "spotify_url": spotify_url}


def controll_user_login(spotify_id, display_name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE spotify_id = %s", (spotify_id,))
    user = cur.fetchone()

    if not user:
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
        user_id = user[0]
        return user_id


def create_subforum_in_db(name, description, creator_id):
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
    subforum_dict = get_subforum_by_name(name)

    if subforum_dict is None:
        return None

    threads = get_threads_by_forum(subforum_dict["id"])

    return {"subforum": subforum_dict, "threads": threads}
