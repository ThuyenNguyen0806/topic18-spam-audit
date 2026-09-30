"""Explainable heuristics. A warning is a lead for manual review, not a penalty verdict."""

import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from urllib.parse import urlsplit


URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
PROMO_RE = re.compile(r"mua ngay|giảm giá|khuyến mãi|ưu đãi|sale|buy now|cheap", re.I)
PLACE_RE = re.compile(r"quận\s*\d+|hà nội|hồ chí minh|đà nẵng|district\s*\d+", re.I)


def normalize(value):
    return " ".join(re.findall(r"\w+", value.casefold(), flags=re.UNICODE))


def warning(kind, pages, evidence, reason, action):
    return {"type": kind, "pages": pages, "evidence": evidence[:220], "reason": reason, "action": action}


def detect_comments(pages):
    results = []
    for page in pages:
        comments = page.get("comments", [])
        counts = Counter(normalize(c) for c in comments if len(normalize(c)) >= 25)
        for comment in comments:
            urls = URL_RE.findall(comment)
            repeated = counts[normalize(comment)] >= 2
            promotional = bool(PROMO_RE.search(comment))
            if (urls and (promotional or len(urls) >= 2)) or repeated:
                reasons = []
                if urls and promotional:
                    reasons.append("có liên kết kèm lời mời quảng cáo")
                if len(urls) >= 2:
                    reasons.append("chứa nhiều liên kết")
                if repeated:
                    reasons.append("lặp lại trong các bình luận")
                results.append(warning("Comment spam", [page["url"]], comment, "Bình luận " + ", ".join(reasons) + ".", "Duyệt hoặc ẩn bình luận; giới hạn liên kết, bật kiểm duyệt và chống gửi lặp."))
    return results


def detect_links(pages):
    results = []
    for page in pages:
        links = page.get("links", [])
        if len(links) < 5:
            continue
        destinations = Counter(urlsplit(link.get("href", "")).netloc.casefold() for link in links)
        top_domain, top_count = destinations.most_common(1)[0]
        promo_count = sum(bool(PROMO_RE.search(link.get("text", ""))) for link in links)
        if top_domain and top_count >= 5 and top_count / len(links) >= .65 and promo_count >= 4:
            examples = ", ".join(link["text"] for link in links[:4])
            results.append(warning("Link spam", [page["url"]], f"{top_count}/{len(links)} liên kết tới {top_domain}; anchor: {examples}", "Nhiều liên kết cùng trỏ về một miền và dùng anchor mang tính quảng cáo.", "Gỡ liên kết không cần thiết; giữ liên kết hữu ích, kiểm tra nguồn và thuộc tính rel phù hợp."))
    return results


def detect_duplicate(pages):
    results = []
    for left, right in combinations(pages, 2):
        a, b = normalize(left.get("text", "")), normalize(right.get("text", ""))
        if min(len(a.split()), len(b.split())) < 35:
            continue
        ratio = SequenceMatcher(None, a, b, autojunk=False).ratio()
        if ratio >= .86:
            results.append(warning("Nội dung trùng lặp", [left["url"], right["url"]], f"Mức giống nhau {ratio:.0%}; đoạn đầu: {left['text'][:125]}", "Hai URL có phần nội dung chính giống nhau ở mức cao.", "Gộp nội dung hoặc viết phần khác biệt có giá trị; cân nhắc canonical hay chuyển hướng khi phù hợp."))
    return results


def detect_doorway(pages):
    results = []
    groups = defaultdict(list)
    for page in pages:
        title = page.get("title", "")
        if not PLACE_RE.search(title):
            continue
        targets = [link.get("href", "") for link in page.get("links", []) if re.search(r"đặt lịch|gọi ngay|mua ngay|đăng ký|book", link.get("text", ""), re.I)]
        if not targets:
            continue
        template = normalize(PLACE_RE.sub("<địa điểm>", page.get("text", "")))
        if len(template.split()) < 20:
            continue
        groups[targets[0]].append((page, template))
    for target, entries in groups.items():
        if len(entries) < 3:
            continue
        similar = all(SequenceMatcher(None, a[1], b[1], autojunk=False).ratio() >= .82 for a, b in combinations(entries, 2))
        if similar:
            results.append(warning("Doorway pages", [item[0]["url"] for item in entries], f"{len(entries)} trang đổi tên địa điểm, nội dung gần giống và cùng dẫn tới {target}", "Cụm trang theo địa điểm có nội dung thay đổi rất ít và cùng hướng người đọc tới một đích.", "Gộp các trang gần như giống nhau hoặc bổ sung thông tin thực sự riêng cho từng địa điểm."))
    return results


def analyze(pages):
    findings = []
    for detector in (detect_comments, detect_links, detect_duplicate, detect_doorway):
        findings.extend(detector(pages))
    return findings
