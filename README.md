# Topic 18 — Web Spam Inspector

Một web Flask tích hợp **đăng bài, bình luận và kiểm tra spam** trong cùng ứng dụng. Người dùng cũng có thể chọn website mẫu hoặc nhập URL công khai. Bộ kiểm tra tìm dấu hiệu nghi vấn về comment spam, link spam, nội dung trùng lặp và doorway pages; không xác nhận tình trạng phạt của Google.

Sau khi xem báo cáo, người quản trị có thể **ẩn hoặc khôi phục** bài viết/bình luận ở `/moderation`. Nội dung bị ẩn không xuất hiện công khai và không được tính trong lần quét tiếp theo. Web không tự động ẩn dựa trên một cảnh báo vì bộ quy tắc có thể báo nhầm.

## Chạy trên máy

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Mở `http://127.0.0.1:5000`. Trên trang chủ, chọn **Bài viết & bình luận** để đăng nội dung, rồi bấm **Kiểm tra web này**. Dữ liệu trên máy được lưu tự động trong `topic18.db` (SQLite). Hai chế độ mẫu và URL vẫn hoạt động độc lập.

### Bật trang quản trị trên Windows (PowerShell trong VS Code)

Nếu web đang chạy, nhấn **Ctrl+C** trong Terminal để dừng. Gõ lần lượt:

```powershell
$env:ADMIN_PASSWORD="chon-mat-khau-rieng-cua-ban"
.\.venv\Scripts\python.exe app.py
```

Mở `http://127.0.0.1:5000/moderation`, đăng nhập bằng mật khẩu vừa đặt. Đổi `chon-mat-khau-rieng-cua-ban` thành mật khẩu do bạn tự chọn; không công khai mật khẩu trong báo cáo, ảnh chụp hoặc GitHub. Biến PowerShell này chỉ tồn tại trong Terminal đang dùng; mỗi lần mở Terminal mới cần đặt lại. **Giữ thư mục và file `topic18.db` cũ** khi cập nhật mã nguồn để bài và bình luận đã đăng còn nguyên.

## Chạy kiểm thử

```bash
python -m unittest discover -s tests -v
```

## Cách hoạt động

| Loại | Quy tắc minh họa | Điều kiện để phân tích |
| --- | --- | --- |
| Comment spam | Bình luận lặp lại hoặc có link quảng cáo / nhiều link | Bình luận hiển thị trong HTML với lớp `.comment`, `.comment-content`, `.comment-body`, `#comments article` hoặc `itemprop=commentText` |
| Link spam | Từ 5 link tới cùng miền, chiếm ít nhất 65% số link và có từ 4 anchor quảng cáo | Link xuất hiện trong nội dung HTML |
| Nội dung trùng lặp | Hai trang từ 35 từ mỗi trang, độ giống nội dung chính từ 86% | Web đọc được từ 2 trang |
| Doorway pages | Từ 3 trang có địa điểm trong tiêu đề, nội dung mẫu gần giống và cùng link đặt lịch | Web đọc được ít nhất 3 trang liên quan |

Nội dung cộng đồng cho phép ghi link trong bài dưới dạng `[Tên liên kết](https://example.com)`. Bộ kiểm tra dùng tên này làm anchor để phân tích link spam và doorway pages. Bài đăng hiển thị dạng văn bản thuần nhằm tránh thực thi HTML do người dùng nhập.

Chế độ URL đọc trang ban đầu và tối đa 5 liên kết cùng hostname, không thực thi JavaScript, không đăng nhập và không quét toàn bộ website. Kết quả có thể bỏ sót hoặc cảnh báo nhầm, cần đối chiếu thủ công. Các giới hạn URL và dung lượng giúp bản demo tránh truy cập mạng nội bộ và tải quá nhiều dữ liệu.

## Đưa lên GitHub và Render

1. Tạo repository mới trên GitHub. Trong thư mục dự án, chạy:

   ```bash
   git init
   git add .
   git commit -m "Build Topic 18 spam audit demo"
   git branch -M main
   git remote add origin https://github.com/TEN_TAI_KHOAN/TEN_REPO.git
   git push -u origin main
   ```

2. Đăng nhập Render → **New → Web Service** → kết nối repository → chọn **Python 3** và gói **Free**. Thiết lập **Build Command** `pip install -r requirements.txt`, **Start Command** `gunicorn app:app`. Render cũng có thể nhận cấu hình trong `render.yaml` nếu chọn Blueprint.
3. **Để bài và bình luận không bị mất khi web khởi động lại**, tạo cơ sở dữ liệu PostgreSQL dùng được lâu dài (chẳng hạn tài khoản PostgreSQL hiện có), rồi đặt biến môi trường `DATABASE_URL` bằng chuỗi kết nối của chính cơ sở dữ liệu ấy trong Render. Đặt thêm `SECRET_KEY` là một chuỗi bí mật dài, cố định và `ADMIN_PASSWORD` là mật khẩu quản trị đủ mạnh. Không ghi ba giá trị này vào GitHub. Ứng dụng tự tạo bảng `posts`, `comments`, `hidden_items` trong lần truy cập đầu.
4. Đợi trạng thái Live, mở URL `https://TEN-DICH-VU.onrender.com` bằng điện thoại hoặc máy khác. Kiểm tra `https://TEN-DICH-VU.onrender.com/health` trả về `{"status":"ok"}`. Đăng bài, bình luận, thử **Kiểm tra web này**, đăng nhập **Quản trị** để ẩn/khôi phục bình luận thử, rồi thử thêm các website mẫu.

**Chú ý về dữ liệu:** Nếu không đặt `DATABASE_URL`, ứng dụng dùng SQLite. SQLite phù hợp để chạy trên máy nhưng file trên Render Free sẽ mất khi dịch vụ khởi động lại hoặc triển khai lại. Render Free có thể tạm dừng web sau 15 phút không hoạt động. Nếu dùng **Render Postgres Free**, cơ sở dữ liệu hiện có thời hạn 30 ngày; cần lên kế hoạch xuất dữ liệu/chuyển sang nơi lưu lâu dài trước khi hết hạn. Có thể dùng PostgreSQL của nhà cung cấp khác nếu cho phép kết nối từ Render.

## Phân chia 3 người

| Thành viên | Tập tin phụ trách | Việc chính |
| --- | --- | --- |
| Người 1 | `detectors.py` (`detect_comments`, `detect_links`) | Dữ liệu và quy tắc bình luận/link, kiểm tra bằng chứng |
| Người 2 | `detectors.py` (`detect_duplicate`, `detect_doorway`) | So sánh nội dung và phát hiện cụm doorway |
| Người 3 | `app.py`, `store.py`, `crawler.py`, `templates/`, `static/` | Giao diện đăng bài/bình luận, SQLite/PostgreSQL, nhập URL, ghép các bộ phát hiện, triển khai |

Mọi hàm phát hiện nhận danh sách `pages`; mỗi trang gồm `url`, `title`, `text`, `comments`, `links`. Đầu ra chung có `type`, `pages`, `evidence`, `reason`, `action`.

## Demo nhanh

1. Vào **Bài viết & bình luận**, tạo bài mới và gửi bình luận quảng cáo. Bấm **Kiểm tra web này** để xem cảnh báo. Vào **Quản trị**, ẩn bình luận; kiểm tra lại để xác nhận cảnh báo đó biến mất. Có thể khôi phục nếu cảnh báo nhầm.
2. Chọn **Blog học tập · bình thường**: không có cảnh báo theo bộ quy tắc.
3. Chọn lần lượt **Bình luận quảng cáo**, **Liên kết nhồi nhét**, **Hai bài viết trùng lặp**, **Trang cửa ngõ theo địa điểm** để demo chắc chắn cả 4 loại.
4. Mở một cảnh báo và giải thích loại, trang, bằng chứng, lý do, cách xử lý.

Xem thêm [BAO_CAO.md](BAO_CAO.md) để chuẩn bị phần thuyết trình.
