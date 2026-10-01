"""Small, bounded public-site crawler for classroom demonstrations."""

import ipaddress
import json
import re
import socket
from urllib.parse import quote, urljoin, urldefrag, urlsplit

import urllib3
from bs4 import BeautifulSoup


MAX_BYTES = 900_000
MAX_PAGES = 6
USER_AGENT = "Topic18ClassDemo/1.0 (bounded public page checker)"
DOH_RESOLVERS = (("1.1.1.1", "cloudflare-dns.com", "/dns-query"), ("8.8.8.8", "dns.google", "/resolve"))


class CrawlError(ValueError):
    pass


def resolve_over_https(hostname):
    """Try a TLS-verified public resolver only if the machine's DNS fails."""
    for ip, service, endpoint in DOH_RESOLVERS:
        addresses = set()
        successful = False
        try:
            pool = urllib3.HTTPSConnectionPool(ip, 443, server_hostname=service, assert_hostname=service, timeout=urllib3.Timeout(connect=2, read=3))
            try:
                for record_type in ("A", "AAAA"):
                    path = f"{endpoint}?name={quote(hostname, safe='')}&type={record_type}"
                    response = pool.urlopen("GET", path, headers={"Host": service, "Accept": "application/dns-json"}, redirect=False, retries=False, preload_content=False)
                    try:
                        if response.status != 200:
                            continue
                        data = json.loads(response.read(16_385))
                        if data.get("Status") != 0:
                            continue
                        successful = True
                        for answer in data.get("Answer", []):
                            if answer.get("type") in (1, 28):
                                addresses.add(str(ipaddress.ip_address(answer["data"])))
                    finally:
                        response.release_conn()
            finally:
                pool.close()
        except (urllib3.exceptions.HTTPError, OSError, ValueError, KeyError, json.JSONDecodeError):
            continue
        if successful and addresses:
            return addresses
    return set()


def checked_address(url):
    try:
        parts = urlsplit(url)
        hostname = parts.hostname
    except ValueError as exc:
        raise CrawlError("URL không đúng định dạng.") from exc
    if parts.scheme not in ("http", "https") or not hostname or parts.username or parts.password:
        raise CrawlError("Chỉ nhập URL http/https công khai, không kèm tài khoản hoặc mật khẩu.")
    try:
        port = parts.port or (443 if parts.scheme == "https" else 80)
    except ValueError as exc:
        raise CrawlError("Cổng trong URL không hợp lệ.") from exc
    if port not in (80, 443):
        raise CrawlError("Bản demo chỉ hỗ trợ cổng 80 và 443.")
    try:
        addresses = {entry[4][0] for entry in socket.getaddrinfo(parts.hostname, port, type=socket.SOCK_STREAM)}
    except (socket.gaierror, UnicodeError):
        addresses = resolve_over_https(parts.hostname)
        if not addresses:
            raise CrawlError("Máy chạy web không phân giải được tên miền này. Hãy thử URL có www hoặc kiểm tra DNS/mạng; trang vẫn có thể mở trong Chrome.")
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise CrawlError("URL phải trỏ tới địa chỉ IP công khai.")
    return parts, sorted(addresses)[0], port


def fetch_html(url):
    """Pin each connection to a validated IP; never follow redirects implicitly."""
    for _ in range(3):
        parts, ip, port = checked_address(url)
        pool_type = urllib3.HTTPSConnectionPool if parts.scheme == "https" else urllib3.HTTPConnectionPool
        options = {"host": ip, "port": port, "timeout": urllib3.Timeout(connect=3, read=5), "maxsize": 1}
        if parts.scheme == "https":
            options.update(server_hostname=parts.hostname, assert_hostname=parts.hostname)
        pool = pool_type(**options)
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        host_header = parts.hostname if port in (80, 443) else f"{parts.hostname}:{port}"
        try:
            response = pool.urlopen("GET", path, headers={"Host": host_header, "User-Agent": USER_AGENT, "Accept": "text/html"}, redirect=False, retries=False, preload_content=False)
            try:
                if response.status in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not location:
                        raise CrawlError("Trang chuyển hướng nhưng không có địa chỉ đích.")
                    next_url = urljoin(url, location)
                    next_host = urlsplit(next_url).hostname
                    if not next_host or next_host.removeprefix("www.") != parts.hostname.removeprefix("www."):
                        raise CrawlError("Trang chuyển hướng sang miền khác; hãy nhập URL đích trực tiếp.")
                    url = next_url
                    continue
                if response.status != 200:
                    raise CrawlError(f"Website trả về HTTP {response.status}.")
                if "text/html" not in response.headers.get("Content-Type", "").lower():
                    raise CrawlError("URL không trả về trang HTML.")
                content = response.read(MAX_BYTES + 1)
                if len(content) > MAX_BYTES:
                    raise CrawlError("Trang vượt giới hạn dung lượng của bản demo.")
                return url, content
            finally:
                response.release_conn()
        except (urllib3.exceptions.HTTPError, TimeoutError, OSError) as exc:
            raise CrawlError("Không đọc được website; hãy kiểm tra URL hoặc thử website mẫu.") from exc
        finally:
            pool.close()
    raise CrawlError("Website chuyển hướng quá nhiều lần.")


def parse_page(url, content):
    soup = BeautifulSoup(content, "html.parser")
    # Some test pages name their counterpart as plain text rather than an anchor.
    referenced_paths = re.findall(r"(?<![\w/])/(?:[a-zA-Z0-9_-]+/)+[a-zA-Z0-9_-]+", soup.get_text(" ", strip=True))[:8]
    title = soup.title.get_text(" ", strip=True) if soup.title else url
    selectors = ".comment, .comment-content, .comment-body, [itemprop='commentText'], #comments article"
    comments = [node.get_text(" ", strip=True)[:500] for node in soup.select(selectors)[:40]]
    for node in soup.select("script, style, nav, footer, header, aside, form, .comment, .comment-content, .comment-body, #comments"):
        node.decompose()
    main = soup.select_one("main, article, [role='main']") or soup.body or soup
    text = main.get_text(" ", strip=True)[:12_000]
    links = [{"text": a.get_text(" ", strip=True)[:100], "href": urljoin(url, a.get("href", ""))} for a in main.select("a[href]")[:120]]
    # Đọc thêm Markdown và URL dạng chữ, không đếm lại link HTML.
    markdown_re = re.compile(r"\[([^\]\n]+)\]\((https?://[^\s<>]+?)\)", re.I)
    plain_url_re = re.compile(r"https?://[^\s<>\"'\]\)]+", re.I)
    for node in main.find_all(string=True):
        if node.find_parent("a"):
            continue
        value = str(node)
        for match in markdown_re.finditer(value):
            if len(links) >= 120:
                break
            links.append({"text": match.group(1)[:100], "href": match.group(2)})
        remaining = markdown_re.sub("", value)
        for match in plain_url_re.finditer(remaining):
            if len(links) >= 120:
                break
            context = remaining[max(0, match.start() - 80):match.start()]
            links.append({"text": context.strip()[-100:],
                          "href": match.group().rstrip(".,;!?")})
    return {"url": url, "title": title[:180], "text": text, "comments": comments, "links": links, "referenced_paths": referenced_paths}


def crawl(start_url):
    if len(start_url) > 2000:
        raise CrawlError("URL quá dài.")
    origin = checked_address(start_url)[0].hostname.removeprefix("www.")
    queue, seen, pages, errors = [start_url], set(), [], []
    while queue and len(pages) < MAX_PAGES:
        url = urldefrag(queue.pop(0)).url
        if url in seen:
            continue
        seen.add(url)
        try:
            final_url, content = fetch_html(url)
            page = parse_page(final_url, content)
            pages.append(page)
            for path in page["referenced_paths"]:
                candidate = urljoin(final_url, path)
                if candidate not in seen and candidate not in queue and len(queue) < MAX_PAGES * 2:
                    queue.insert(0, candidate)
            for link in page["links"]:
                candidate = urldefrag(link["href"]).url
                part = urlsplit(candidate)
                if part.scheme in ("http", "https") and part.hostname and part.hostname.removeprefix("www.") == origin and candidate not in seen and candidate not in queue and len(queue) < MAX_PAGES * 2:
                    queue.append(candidate)
        except CrawlError as exc:
            errors.append(f"{url[:100]}: {exc}")
            if not pages and url == start_url:
                raise
    return pages, errors
