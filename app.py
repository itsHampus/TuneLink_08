import psycopg2
import psycopg2.extras

def get_connection():
    return psycopg2.connect(
        dbname = "tunelink",
        user="aq1970",
        password="0q1qfscs",
        host = "pgserver.mau.se",
        port="5432"
)

def get_forum_by_name(name:str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id , name, description FROM forums WHERE name = %s", (name,))
    forum = cur.fetchone()
    cur.close()
    conn.close()
    print("Forum:", forum)
    if forum:
        return {"id": forum [0], "name": forum[1], "description" : forum[2]}
    else:
        return None

def get_threads_by_name(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id , name, description FROM forums WHERE name = %s", (name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2]
        }
    return None

def get_threads_by_forum(forum_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT threads.id, threads.forum_id, threads.creator_id, threads.title, 
               threads.spotify_url, threads.description, threads.is_pinned, 
               threads.created_at, threads.updated_at, 
               users.username 
        FROM threads 
        JOIN users ON threads.creator_id = users.id
        WHERE forum_id = %s
        ORDER BY threads.created_at DESC
    """, (forum_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    threads = []
    for row in rows:
        #i named it trad because python is behing strangely if it's named thread
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


# function that creates post
def create_comment(thread_id, user_id, description, spotify_url=None):
    conn = get_connection()
    with conn.cursor() as cur:
        print(thread_id, user_id, description, spotify_url)
        cur.execute("""
            INSERT INTO t_comments (thread_id, user_id, description, spotify_url, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (thread_id, user_id, description, spotify_url))
        conn.commit()

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


def add_comment(thread_id, user_id, description, spotify_url=None):
    conn = get_db_connection()
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


def get_comments_for_thread(thread_id):
    conn = get_db_connection()
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
