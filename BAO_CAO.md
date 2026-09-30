# BÁO CÁO ĐỒ ÁN — TOPIC 18

**Đề tài:** Xây dựng website phát hiện dấu hiệu spam trên website  
**Lớp:** ........................................ **Nhóm:** ........................  
**Thành viên / MSSV:** ........................................................................

## 1. Mục tiêu và phạm vi

Nhóm xây dựng một web online bằng Python Flask, HTML/CSS để **đăng bài, bình luận và kiểm tra spam trong cùng website**. Người dùng có thể kiểm tra nội dung đã đăng, chọn website mẫu hoặc nhập URL công khai. Bộ phát hiện rà soát bốn dấu hiệu: comment spam, link spam, nội dung trùng lặp và doorway pages. Mỗi cảnh báo hiển thị **loại – trang liên quan – bằng chứng – lý do – cách xử lý**. Đây là nhận diện theo quy tắc để hỗ trợ đánh giá; không xác định website đã bị Google phạt.

Sau khi phát hiện, người quản trị đăng nhập bằng mật khẩu riêng để **ẩn bài viết hoặc bình luận vi phạm**; có thể khôi phục nếu kết luận ban đầu sai. Bộ quy tắc không tự động ẩn vì cảnh báo có thể nhầm lẫn.

## 2. Kiến trúc và dữ liệu

Trình duyệt gửi bài viết và bình luận đến Flask. `store.py` lưu dữ liệu trong SQLite khi chạy trên máy hoặc PostgreSQL khi triển khai online có `DATABASE_URL`. Nút **Kiểm tra web này** đọc bài, bình luận và link từ cơ sở dữ liệu. Sau khi xem cảnh báo, quản trị viên có thể ẩn/khôi phục nội dung; trạng thái ẩn lưu trong bảng `hidden_items`. Với URL bên ngoài, bộ đọc HTML tải trang đầu cùng tối đa năm liên kết cùng hostname rồi trích tiêu đề, nội dung chính, bình luận và liên kết. Với website mẫu, dữ liệu đã được lưu trong `samples.py`. Bốn hàm trong `detectors.py` xử lý cùng một định dạng trang và trả về các cảnh báo có cấu trúc thống nhất. Flask đưa cảnh báo vào trang kết quả.

Web không yêu cầu tài khoản. Các bài và bình luận do người dùng gửi được lưu vào cơ sở dữ liệu. Website mẫu có một trường hợp bình thường và bốn trường hợp nghi vấn, dùng để demo ổn định khi trang ngoài chặn đọc nội dung.

## 3. Bốn loại dấu hiệu và biện pháp ngăn chặn

| Loại | Dấu hiệu quan sát | Biện pháp đề xuất |
| --- | --- | --- |
| Comment spam | Bình luận lặp lại, link quảng cáo, nhiều link | Duyệt bình luận, giới hạn link và tần suất, chống gửi lặp |
| Link spam | Nhiều anchor quảng cáo trỏ cùng một miền | Xóa link không hữu ích, rà soát biên tập, gắn thuộc tính rel khi phù hợp |
| Nội dung trùng lặp | Hai URL có nội dung chính giống nhau ở mức cao | Gộp bài, bổ sung nội dung riêng, cân nhắc canonical/chuyển hướng |
| Doorway pages | Nhiều trang đổi địa điểm nhưng nội dung tương tự và dẫn về cùng đích | Gộp trang hoặc tạo thông tin thực sự hữu ích riêng cho mỗi địa điểm |

## 4. Quy trình thử nghiệm

| Ca thử | Dữ liệu bình thường | Dữ liệu nghi vấn | Kết quả mong đợi |
| --- | --- | --- | --- |
| Comment spam | Bình luận trao đổi trong mẫu clean | Mẫu comment có quảng cáo và lặp | Chỉ cảnh báo mẫu comment |
| Link spam | Link tài liệu tham khảo trong mẫu clean | Mẫu links chứa 8 link quảng cáo cùng đích | Chỉ cảnh báo mẫu links |
| Trùng lặp | Các bài khác chủ đề trong mẫu clean | Mẫu duplicate đăng lại một đoạn dài | Chỉ cảnh báo cặp bài trùng lặp |
| Doorway pages | Các trang clean có chủ đề riêng | Mẫu doorway đổi tên Quận 1, 3, 5 | Cảnh báo cụm 3 trang |

Chạy `python -m unittest discover -s tests -v` để kiểm tra logic, giao diện, luồng đăng bài/bình luận, cách hiển thị nội dung an toàn, thao tác ẩn/khôi phục của quản trị và từ chối URL mạng nội bộ. Với URL ngoài, nhóm cần thử trên một trang công khai được phép truy cập, quan sát số trang đọc được và các lỗi nếu có.

## 5. Hạn chế và hướng phát triển

Quy tắc dựa trên từ khóa, số lượng và độ giống văn bản nên có thể bỏ sót hoặc cảnh báo nhầm. Chế độ URL không chạy JavaScript, không đăng nhập và chỉ đọc tối đa sáu trang nên chưa kiểm tra được toàn bộ website. Nếu chạy SQLite trên Render Free, bài và bình luận có thể mất sau khi dịch vụ khởi động lại; bản online cần PostgreSQL để lưu ổn định. Bước sau có thể thêm xác thực, kiểm duyệt nội dung, chính sách tôn trọng robots, lọc boilerplate tốt hơn và trang quản trị.

## 6. Kịch bản trình diễn

Mở web công khai trên máy hoặc điện thoại. Đăng một bài, gửi bình luận quảng cáo và bấm **Kiểm tra web này**. Đăng nhập trang quản trị, ẩn bình luận rồi kiểm tra lại để minh họa cách xử lý. Chọn mẫu bình thường để đối chiếu, sau đó thử lần lượt bốn mẫu spam. Ở mỗi kết quả, chỉ ra loại, URL, bằng chứng, lý do và cách xử lý. Kết thúc bằng việc nhập một URL công khai và giải thích giới hạn khi website ngoài không hiển thị bình luận hoặc tải dữ liệu động.
