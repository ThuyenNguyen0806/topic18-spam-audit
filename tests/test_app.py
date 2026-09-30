import unittest
import os
import tempfile
from unittest.mock import patch

from app import app
from crawler import CrawlError, checked_address, parse_page
from detectors import analyze
from samples import SAMPLES
from store import add_post, audit_pages


class DetectorTests(unittest.TestCase):
    def test_all_four_scenarios_and_clean_sample(self):
        expected = {"comment": "Comment spam", "links": "Link spam", "duplicate": "Nội dung trùng lặp", "doorway": "Doorway pages"}
        self.assertEqual(analyze(SAMPLES["clean"]["pages"]), [])
        for key, kind in expected.items():
            with self.subTest(case=key):
                findings = analyze(SAMPLES[key]["pages"])
                matching = [f for f in findings if f["type"] == kind]
                self.assertTrue(matching)
                for item in matching:
                    self.assertTrue(all(item[field] for field in ("pages", "evidence", "reason", "action")))

    def test_no_false_positive_for_small_ordinary_links(self):
        self.assertFalse(any(f["type"] == "Link spam" for f in analyze(SAMPLES["clean"]["pages"])))

    def test_parse_static_html_comments(self):
        page = parse_page("https://example.com/post", b"<html><head><title>Demo</title></head><body><main><p>Content</p><a href='/next'>Read</a></main><div class='comment'>Hello there</div></body></html>")
        self.assertEqual(page["comments"], ["Hello there"])
        self.assertEqual(page["links"][0]["href"], "https://example.com/next")


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path_patch = patch.dict(os.environ, {"SQLITE_PATH": os.path.join(self.tempdir.name, "test.db"), "DATABASE_URL": ""})
        self.path_patch.start()
        self.client = app.test_client()

    def tearDown(self):
        self.path_patch.stop()
        self.tempdir.cleanup()

    def csrf(self):
        self.client.get("/community")
        with self.client.session_transaction() as session:
            return session["csrf"]

    def test_home_and_report(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        clean = self.client.post("/check", data={"mode": "sample", "sample": "clean"})
        self.assertIn("Chưa tìm thấy dấu hiệu".encode(), clean.data)
        for kind in ("comment", "links", "duplicate", "doorway"):
            with self.subTest(kind=kind):
                response = self.client.post("/check", data={"mode": "sample", "sample": kind})
                self.assertEqual(response.status_code, 200)
                self.assertIn("BẰNG CHỨNG".encode(), response.data)
                self.assertIn("CÁCH XỬ LÝ".encode(), response.data)

    def test_private_addresses_refused(self):
        for url in ("http://127.0.0.1", "http://localhost", "http://192.168.1.10", "file:///etc/passwd", "http://["):
            with self.subTest(url=url), self.assertRaises(CrawlError):
                checked_address(url)

    def test_url_error_is_shown(self):
        with patch("app.crawl", side_effect=CrawlError("Không đọc được website.")):
            response = self.client.post("/check", data={"mode": "url", "url": "https://example.com"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Không đọc được website".encode(), response.data)

    def test_publish_comment_and_audit_own_website(self):
        token = self.csrf()
        published = self.client.post("/posts", data={"csrf": token, "author": "Sinh viên", "title": "Chia sẻ cách học Python", "body": "Mỗi ngày tôi luyện tập Python bằng các bài toán nhỏ, đọc tài liệu và thử sửa các lỗi trong chương trình."})
        self.assertEqual(published.status_code, 302)
        self.assertEqual(published.location.split("/")[-1], "1")
        for _ in range(2):
            comment = self.client.post("/posts/1/comments", data={"csrf": token, "author": "Bạn đọc", "body": "Mua hàng giảm giá ngay https://sale.example/deal! Mua hàng giảm giá ngay https://sale.example/deal!"})
            self.assertEqual(comment.status_code, 302)
        page = self.client.get("/posts/1")
        self.assertIn("Sinh viên".encode(), page.data)
        report = self.client.post("/check", data={"mode": "community"})
        self.assertIn(b"Comment spam", report.data)
        self.assertIn(b"/posts/1", report.data)

    def test_post_content_is_escaped_and_csrf_required(self):
        no_token = self.client.post("/posts", data={"author": "Someone", "title": "Valid title", "body": "Content long enough to satisfy the requirements for a simple article."})
        self.assertEqual(no_token.status_code, 400)
        token = self.csrf()
        self.client.post("/posts", data={"csrf": token, "author": "Someone", "title": "Valid title", "body": "<script>alert(1)</script> Content long enough to satisfy the requirements for an article."})
        response = self.client.get("/posts/1")
        self.assertNotIn(b"<script>", response.data)
        self.assertIn(b"&lt;script&gt;", response.data)

    def test_audit_stored_posts_all_other_types(self):
        for post in SAMPLES["duplicate"]["pages"]:
            add_post(post["title"], post["text"], "Nhóm")
        link_post = SAMPLES["links"]["pages"][0]
        add_post(link_post["title"], "\n".join(f"[{item['text']}]({item['href']})" for item in link_post["links"]), "Nhóm")
        for post in SAMPLES["doorway"]["pages"]:
            add_post(post["title"], post["text"] + " [Đặt lịch ngay](https://booking.example/landing)", "Nhóm")
        findings = analyze(audit_pages("https://topic18.example"))
        for kind in ("Nội dung trùng lặp", "Link spam", "Doorway pages"):
            with self.subTest(kind=kind):
                self.assertIn(kind, [item["type"] for item in findings])

    def test_admin_hides_and_restores_spam_without_deleting_data(self):
        with patch.dict(os.environ, {"ADMIN_PASSWORD": "local-test-password"}):
            token = self.csrf()
            self.client.post("/posts", data={"csrf": token, "author": "Sinh viên", "title": "Bài viết thử nghiệm", "body": "Tôi viết một bài học tập đủ dài để thử khả năng kiểm duyệt nội dung trong website này."})
            self.client.post("/posts/1/comments", data={"csrf": token, "author": "Quảng cáo", "body": "Mua ngay giảm giá https://sale.example/deal"})
            self.assertIn(b"Comment spam", self.client.post("/check", data={"mode": "community"}).data)
            self.assertEqual(self.client.post("/moderation/comment/1/hide", data={"csrf": token}).status_code, 403)
            self.assertEqual(self.client.post("/moderation/login", data={"csrf": token, "password": "wrong"}).status_code, 401)
            self.assertEqual(self.client.post("/moderation/login", data={"csrf": token, "password": "local-test-password"}).status_code, 302)
            self.assertEqual(self.client.post("/moderation/comment/1/hide", data={"csrf": token}).status_code, 302)
            self.assertNotIn(b"Comment spam", self.client.post("/check", data={"mode": "community"}).data)
            self.assertNotIn("Mua ngay giảm giá".encode(), self.client.get("/posts/1").data)
            self.assertEqual(self.client.post("/moderation/comment/1/restore", data={"csrf": token}).status_code, 302)
            self.assertIn(b"Comment spam", self.client.post("/check", data={"mode": "community"}).data)


if __name__ == "__main__":
    unittest.main()
