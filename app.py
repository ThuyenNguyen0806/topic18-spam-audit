import os
import secrets
import time
import hmac
import hashlib
from collections import defaultdict, deque

from flask import Flask, abort, redirect, render_template, request, session, url_for

from crawler import CrawlError, crawl
from detectors import analyze
from samples import SAMPLES
from store import add_comment, add_post, audit_pages, get_post, list_posts, moderation_items, set_hidden


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10_000
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
_writes = defaultdict(deque)


def form_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(24)
    return session["csrf"]


app.jinja_env.globals["form_token"] = form_token


def accept_write():
    if request.form.get("website", "") or not session.get("csrf") or not secrets.compare_digest(request.form.get("csrf", ""), session["csrf"]):
        abort(400)
    now = time.monotonic()
    ip = request.remote_addr or "unknown"
    recent = _writes[ip]
    while recent and now - recent[0] > 3600:
        recent.popleft()
    if len(recent) >= 15:
        abort(429, description="Bạn đã gửi quá nhiều nội dung. Vui lòng thử lại sau.")
    recent.append(now)


def clean_field(name, limit):
    value = request.form.get(name, "").strip()
    if len(value) > limit:
        abort(400, description=f"Trường {name} quá dài.")
    return value


def admin_ready():
    return bool(os.getenv("ADMIN_PASSWORD"))


def admin_logged_in():
    if not admin_ready():
        return False
    expected = hmac.new(app.secret_key.encode(), os.environ["ADMIN_PASSWORD"].encode(), hashlib.sha256).hexdigest()
    return secrets.compare_digest(session.get("admin_signature", ""), expected)


@app.get("/")
def home():
    return render_template("index.html", samples=SAMPLES)


@app.get("/community")
def community():
    return render_template("community.html", posts=list_posts())


@app.post("/posts")
def create_post():
    accept_write()
    title, body, author = clean_field("title", 150), clean_field("body", 6000), clean_field("author", 60)
    if len(title) < 5 or len(body) < 40 or len(author) < 2:
        abort(400, description="Tên cần từ 2 ký tự, tiêu đề từ 5 ký tự và nội dung từ 40 ký tự.")
    post_id = add_post(title, body, author)
    return redirect(url_for("view_post", post_id=post_id))


@app.get("/posts/<int:post_id>")
def view_post(post_id):
    post, comments = get_post(post_id)
    if post is None:
        abort(404)
    return render_template("post.html", post=post, comments=comments)


@app.post("/posts/<int:post_id>/comments")
def create_comment(post_id):
    accept_write()
    author, body = clean_field("author", 60), clean_field("body", 500)
    if len(author) < 2 or len(body) < 3:
        abort(400, description="Tên cần từ 2 ký tự và bình luận từ 3 ký tự.")
    if not add_comment(post_id, author, body):
        abort(404)
    return redirect(url_for("view_post", post_id=post_id) + "#comments")


@app.get("/moderation")
def moderation():
    if not admin_ready():
        return render_template("moderation.html", disabled=True), 503
    if not admin_logged_in():
        return render_template("moderation.html")
    posts, comments = moderation_items()
    return render_template("moderation.html", posts=posts, comments=comments, logged_in=True)


@app.post("/moderation/login")
def moderation_login():
    if not admin_ready():
        abort(503)
    accept_write()
    supplied = request.form.get("password", "")
    if not secrets.compare_digest(supplied, os.environ["ADMIN_PASSWORD"]):
        return render_template("moderation.html", error="Mật khẩu quản trị không đúng."), 401
    session["admin_signature"] = hmac.new(app.secret_key.encode(), os.environ["ADMIN_PASSWORD"].encode(), hashlib.sha256).hexdigest()
    return redirect(url_for("moderation"))


@app.post("/moderation/logout")
def moderation_logout():
    if not session.get("csrf") or not secrets.compare_digest(request.form.get("csrf", ""), session["csrf"]):
        abort(400)
    session.pop("admin_signature", None)
    return redirect(url_for("moderation"))


@app.post("/moderation/<kind>/<int:item_id>/<action>")
def moderation_action(kind, item_id, action):
    if not admin_logged_in():
        abort(403)
    if not session.get("csrf") or not secrets.compare_digest(request.form.get("csrf", ""), session["csrf"]):
        abort(400)
    if action not in ("hide", "restore") or not set_hidden(kind, item_id, action == "hide"):
        abort(404)
    return redirect(url_for("moderation"))


@app.post("/check")
def check():
    mode = request.form.get("mode", "sample")
    sample_key = request.form.get("sample", "clean")
    url = request.form.get("url", "").strip()
    if mode == "sample":
        if sample_key not in SAMPLES:
            return render_template("index.html", samples=SAMPLES, error="Mẫu đã chọn không tồn tại."), 400
        source = SAMPLES[sample_key]
        pages, errors, name = source["pages"], [], source["name"]
    elif mode == "community":
        pages, errors, name = audit_pages(request.url_root.rstrip("/")), [], "Bài viết và bình luận trên web này"
    elif mode == "url":
        if not url:
            return render_template("index.html", samples=SAMPLES, error="Hãy nhập một URL công khai."), 400
        try:
            pages, errors = crawl(url)
        except CrawlError as exc:
            return render_template("index.html", samples=SAMPLES, error=str(exc), submitted_url=url), 400
        name = url
    else:
        return render_template("index.html", samples=SAMPLES, error="Chế độ kiểm tra không hợp lệ."), 400
    findings = analyze(pages)
    return render_template("results.html", findings=findings, pages=pages, errors=errors, name=name, mode=mode)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=False)
