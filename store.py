"""SQLite locally; set DATABASE_URL for a persistent PostgreSQL deployment."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def is_postgres():
    return bool(os.getenv("DATABASE_URL", "").startswith(("postgres://", "postgresql://")))


@contextmanager
def connect():
    if is_postgres():
        import psycopg
        from psycopg.rows import dict_row

        connection = psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
    else:
        path = Path(os.getenv("SQLITE_PATH", Path(__file__).with_name("topic18.db")))
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def run(conn, sql, values=()):
    return conn.execute(sql.replace("?", "%s") if is_postgres() else sql, values)


def init_db(conn):
    primary_key = "BIGSERIAL PRIMARY KEY" if is_postgres() else "INTEGER PRIMARY KEY AUTOINCREMENT"
    run(conn, f"CREATE TABLE IF NOT EXISTS posts (id {primary_key}, title TEXT NOT NULL, body TEXT NOT NULL, author TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    run(conn, f"CREATE TABLE IF NOT EXISTS comments (id {primary_key}, post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE, author TEXT NOT NULL, body TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    run(conn, "CREATE TABLE IF NOT EXISTS hidden_items (kind TEXT NOT NULL, item_id BIGINT NOT NULL, PRIMARY KEY(kind,item_id))")


def list_posts():
    with connect() as conn:
        init_db(conn)
        return [dict(row) for row in run(conn, "SELECT p.*, (SELECT COUNT(*) FROM comments c WHERE c.post_id=p.id AND NOT EXISTS (SELECT 1 FROM hidden_items h WHERE h.kind='comment' AND h.item_id=c.id)) AS comment_count FROM posts p WHERE NOT EXISTS (SELECT 1 FROM hidden_items h WHERE h.kind='post' AND h.item_id=p.id) ORDER BY p.id DESC LIMIT 100").fetchall()]


def get_post(post_id):
    with connect() as conn:
        init_db(conn)
        post = run(conn, "SELECT * FROM posts WHERE id=? AND NOT EXISTS (SELECT 1 FROM hidden_items h WHERE h.kind='post' AND h.item_id=posts.id)", (post_id,)).fetchone()
        if post is None:
            return None, []
        comments = run(conn, "SELECT * FROM comments WHERE post_id=? AND NOT EXISTS (SELECT 1 FROM hidden_items h WHERE h.kind='comment' AND h.item_id=comments.id) ORDER BY id", (post_id,)).fetchall()
        return dict(post), [dict(row) for row in comments]


def add_post(title, body, author):
    with connect() as conn:
        init_db(conn)
        if is_postgres():
            return run(conn, "INSERT INTO posts(title,body,author) VALUES(?,?,?) RETURNING id", (title, body, author)).fetchone()["id"]
        return run(conn, "INSERT INTO posts(title,body,author) VALUES(?,?,?)", (title, body, author)).lastrowid


def add_comment(post_id, author, body):
    with connect() as conn:
        init_db(conn)
        exists = run(conn, "SELECT id FROM posts WHERE id=? AND NOT EXISTS (SELECT 1 FROM hidden_items h WHERE h.kind='post' AND h.item_id=posts.id)", (post_id,)).fetchone()
        if not exists:
            return False
        run(conn, "INSERT INTO comments(post_id,author,body) VALUES(?,?,?)", (post_id, author, body))
        return True


def audit_pages(base_url):
    from detectors import URL_RE
    import re

    markdown_link = re.compile(r"\[([^\]]{1,100})\]\((https?://[^\s)]+)\)", re.I)
    with connect() as conn:
        init_db(conn)
        posts = run(conn, "SELECT id,title,body FROM posts WHERE NOT EXISTS (SELECT 1 FROM hidden_items h WHERE h.kind='post' AND h.item_id=posts.id) ORDER BY id DESC LIMIT 100").fetchall()
        comments = run(conn, "SELECT post_id,body FROM comments WHERE post_id IN (SELECT id FROM posts WHERE NOT EXISTS (SELECT 1 FROM hidden_items h WHERE h.kind='post' AND h.item_id=posts.id) ORDER BY id DESC LIMIT 100) AND NOT EXISTS (SELECT 1 FROM hidden_items h WHERE h.kind='comment' AND h.item_id=comments.id) ORDER BY id").fetchall()
    grouped = {}
    for item in comments:
        grouped.setdefault(item["post_id"], []).append(item["body"])
    pages = []
    for post in posts:
        body = post["body"]
        links = [{"text": label, "href": href} for label, href in markdown_link.findall(body)]
        links.extend({"text": "liên kết trong bài", "href": href} for href in URL_RE.findall(markdown_link.sub("", body)))
        pages.append({"url": f"{base_url}/posts/{post['id']}", "title": post["title"], "text": markdown_link.sub(lambda m: m.group(1), body), "comments": grouped.get(post["id"], []), "links": links})
    return pages


def moderation_items():
    with connect() as conn:
        init_db(conn)
        posts = [dict(row) for row in run(conn, "SELECT p.id,p.title,p.author,p.body, EXISTS(SELECT 1 FROM hidden_items h WHERE h.kind='post' AND h.item_id=p.id) AS hidden FROM posts p ORDER BY id DESC LIMIT 100").fetchall()]
        comments = [dict(row) for row in run(conn, "SELECT c.id,c.post_id,c.author,c.body, EXISTS(SELECT 1 FROM hidden_items h WHERE h.kind='comment' AND h.item_id=c.id) AS hidden FROM comments c ORDER BY id DESC LIMIT 100").fetchall()]
        return posts, comments


def set_hidden(kind, item_id, hidden):
    if kind not in ("post", "comment"):
        return False
    table = "posts" if kind == "post" else "comments"
    with connect() as conn:
        init_db(conn)
        if not run(conn, f"SELECT id FROM {table} WHERE id=?", (item_id,)).fetchone():
            return False
        if hidden:
            run(conn, "INSERT INTO hidden_items(kind,item_id) VALUES(?,?) ON CONFLICT DO NOTHING", (kind, item_id))
        else:
            run(conn, "DELETE FROM hidden_items WHERE kind=? AND item_id=?", (kind, item_id))
        return True
