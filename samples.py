"""Self-contained demonstration websites; never rely on third-party pages for demos."""

SAMPLES = {
    "clean": {
        "name": "Blog học tập · bình thường",
        "description": "Ba bài độc lập với bình luận tự nhiên và liên kết tham khảo.",
        "pages": [
            {"url": "https://mau.local/bai-viet/python-co-ban", "title": "Học Python cơ bản", "text": "Python là ngôn ngữ lập trình dễ tiếp cận. Bài học này giới thiệu biến, kiểu dữ liệu và câu lệnh điều kiện. Người học có thể luyện tập bằng các chương trình ngắn.", "comments": ["Bài hướng dẫn rất dễ hiểu, cảm ơn tác giả!", "Mình muốn tìm thêm ví dụ về vòng lặp."], "links": [{"text": "Tài liệu Python", "href": "https://docs.python.org/3/"}]},
            {"url": "https://mau.local/bai-viet/mang-may-tinh", "title": "Nhập môn mạng máy tính", "text": "Mạng máy tính kết nối các thiết bị để trao đổi thông tin. Địa chỉ IP xác định điểm đến còn giao thức TCP giúp chuyển dữ liệu tin cậy giữa các máy.", "comments": ["Phần giải thích địa chỉ IP rất hữu ích."], "links": [{"text": "Trang chủ", "href": "https://mau.local/"}]},
            {"url": "https://mau.local/bai-viet/an-toan-web", "title": "An toàn khi dùng web", "text": "Khi xây dựng website cần xác thực đầu vào và giới hạn quyền truy cập. Quản trị viên nên sao lưu dữ liệu, cập nhật phần mềm và theo dõi nhật ký lỗi thường xuyên.", "comments": [], "links": [{"text": "Đọc bài Python", "href": "https://mau.local/bai-viet/python-co-ban"}]},
        ],
    },
    "comment": {
        "name": "Bình luận quảng cáo",
        "description": "Một bài viết bị chèn bình luận lặp lại chứa liên kết quảng cáo.",
        "pages": [{"url": "https://mau.local/blog/binh-luan", "title": "Thảo luận học lập trình", "text": "Bài viết chia sẻ cách tự học lập trình từ những ví dụ nhỏ và thực hành hằng ngày.", "comments": ["Cảm ơn bài viết, mình đã thử ví dụ.", "Mua hàng giảm giá ngay https://sale.example/deal! Mua hàng giảm giá ngay https://sale.example/deal!", "Mua hàng giảm giá ngay https://sale.example/deal! Mua hàng giảm giá ngay https://sale.example/deal!"], "links": []}],
    },
    "links": {
        "name": "Liên kết nhồi nhét",
        "description": "Trang gắn dày đặc liên kết cùng đích với anchor quảng cáo.",
        "pages": [{"url": "https://mau.local/blog/uu-dai", "title": "Góc chia sẻ", "text": "Trang này giới thiệu vài ghi chú ngắn về chủ đề học tập. Nội dung chính vẫn đang được cập nhật thêm.", "comments": [], "links": [{"text": label, "href": "https://offers.example/buy"} for label in ["mua ngay giá rẻ", "giảm giá sốc", "mua ngay giá rẻ", "khuyến mãi cực sốc", "mua ngay giá rẻ", "mua hàng ưu đãi", "giảm giá sốc", "mua ngay giá rẻ"]]}],
    },
    "duplicate": {
        "name": "Hai bài viết trùng lặp",
        "description": "Hai URL khác nhau đăng lại gần như cùng một đoạn nội dung.",
        "pages": [
            {"url": "https://mau.local/blog/hoc-python-a", "title": "Hướng dẫn tự học Python A", "text": "Để bắt đầu học Python, người học nên cài đặt môi trường, làm quen với biến và kiểu dữ liệu, thực hành câu lệnh điều kiện, vòng lặp và hàm. Mỗi ngày hãy giải một bài tập nhỏ, đọc thông báo lỗi rồi sửa chương trình. Việc luyện tập đều đặn giúp củng cố kiến thức và hình thành tư duy lập trình.", "comments": [], "links": []},
            {"url": "https://mau.local/blog/hoc-python-b", "title": "Hướng dẫn tự học Python B", "text": "Để bắt đầu học Python, người học nên cài đặt môi trường, làm quen với biến và kiểu dữ liệu, thực hành câu lệnh điều kiện, vòng lặp và hàm. Mỗi ngày hãy giải một bài tập nhỏ, đọc thông báo lỗi rồi sửa chương trình. Việc luyện tập đều đặn giúp củng cố kiến thức và hình thành tư duy lập trình.", "comments": [], "links": []},
        ],
    },
    "doorway": {
        "name": "Trang cửa ngõ theo địa điểm",
        "description": "Ba trang đổi tên địa điểm nhưng dùng chung nội dung và cùng chuyển khách về một nơi.",
        "pages": [{"url": f"https://mau.local/dich-vu/{slug}", "title": f"Dịch vụ sửa máy lạnh tại {city}", "text": f"Dịch vụ sửa máy lạnh tại {city}. Đội ngũ hỗ trợ tận nơi, nhận lịch nhanh và báo giá trước khi thực hiện. Gọi ngay để nhận tư vấn và đặt lịch sửa chữa phù hợp với nhu cầu của bạn.", "comments": [], "links": [{"text": "Đặt lịch ngay", "href": "https://booking.example/landing"}]} for slug, city in [("quan-1", "Quận 1"), ("quan-3", "Quận 3"), ("quan-5", "Quận 5")]],
    },
}
