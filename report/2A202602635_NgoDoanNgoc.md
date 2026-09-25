# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | **Ngọ Doãn Ngọc** |
| MSSV | **2A202602635** |
| Khóa/Lớp | K4 |
| Tên nhóm | Nhóm ATri - Day 10 |
| Vai trò chính | **Data Foundation & Recovery Owner** |
| Repository | https://github.com/VoDucTri/K4-L3A-Day10-ATri-Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-09-25 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Raw Ingestion & Dual-Mode | `src/ingestion/crossref.py`<br>`fetch_source_records`, `parse_crossref_payload` | Crossref REST API hoặc snapshot local | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json` | Hoàn thành |
| Data Cleaning & Modeling | `src/ingestion/cleaning.py`<br>`build_clean_dataframe` | `PaperRecord` từ raw json | `data/clean/papers_clean.csv`<br>`data/clean/papers_clean.json` | Hoàn thành |
| Synthetic Corruption Suite | `src/ingestion/corruption.py`<br>`corrupt_clean_dataframe` | Cleaned DataFrame | `data/clean/papers_clean_corrupted.csv`<br>`data/results/corruption_log.json` | Hoàn thành |
| Idempotent Data Repair | `src/ingestion/corruption.py`<br>`repair_clean_dataframe` | Raw records snapshot | `data/clean/papers_clean_repaired.csv` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Cung cấp schema dữ liệu sạch | Võ Đức Trí (`src/observability/quality.py`) | Giúp thiết lập đúng 4 Expectations trong Great Expectations 1.x |
| Kiểm tra tương thích metadata | Đỗ Hoàng Nam Khánh (`src/retrieval/index.py`) | Đảm bảo metadata chứa đủ các trường `authors_joined`, `categories_joined` để truy vấn |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Ingestion dữ liệu thô | `src/ingestion/crossref.py` | 24 bài báo tải về thành công (có fallback offline khi dính lỗi 429) | `data/raw/crossref_records.json` đầy đủ 24 bản ghi |
| Làm sạch và tiền xử lý | `src/ingestion/cleaning.py` | Bóc tách text, xóa thẻ HTML/JATS XML rác, tính `age_days` | `data/clean/papers_clean.csv` 24 dòng sạch |
| Tiêm 6 kịch bản lỗi dữ liệu | `src/ingestion/corruption.py` | Xóa summary, chèn noise, làm cũ ngày, nhân bản dòng | `data/results/corruption_log.json` ghi nhận đủ 6 loại |
| Phục hồi dữ liệu an toàn | `repair_clean_dataframe` | Tái tạo dữ liệu sạch 100% từ raw preservation | `papers_clean_repaired.csv` phục hồi 24 dòng chuẩn |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Dữ liệu thu thập từ bên thứ ba (APIs học thuật) thường chứa nhiều thẻ rác định dạng XML/HTML, khoảng trắng thừa, bản ghi thiếu trường bắt buộc hoặc dính rate-limit 429. Hơn nữa, để kiểm thử độ bền của RAG, cần chủ động tiêm các lỗi dữ liệu thực tế và thiết kế cơ chế tự phục hồi mà không phụ thuộc vào can thiệp thủ công.

### Cách triển khai
1. **Cơ chế Cứu hộ Offline (Dual-Mode):** Thiết kế hàm fetch dữ liệu có timeout và tự động chuyển sang đọc snapshot mẫu `data/raw/crossref_response.json` khi dính mã lỗi 429 hoặc mất kết nối mạng.
2. **Nguyên tắc Raw Preservation:** Tuyệt đối không can thiệp hay sửa đổi file response thô ban đầu, lưu trữ đầy đủ `crossref_response.json` và `crossref_records.json` để làm bằng chứng truy vết nguồn gốc (Data Lineage).
3. **Quy tắc làm sạch dữ liệu:**
   - Dùng biểu thức chính quy (Regex) bóc tách toàn bộ thẻ `<jats:p>` trong abstract.
   - Ghép nối trường `text_for_embedding` theo cấu trúc 5 thành phần: Title, Authors, Published, Categories, Summary.
   - Tính toán `age_days = (run_date - published).days` để phục vụ đo lường Freshness SLA.
4. **Bộ tiêm 6 độc tố dữ liệu (Synthetic Corruption Suite):**
   - *Drop latest:* Loại bỏ 4 bài báo mới nhất.
   - *Blank summary:* Xóa rỗng tóm tắt ở 4 bản ghi.
   - *Inject noise:* Chèn chuỗi ký tự rác vào `text_for_embedding`.
   - *Truncate title:* Cắt ngắn tiêu đề xuống dưới 10 ký tự.
   - *Stale date:* Đổi ngày xuất bản về 5 năm trước (2021).
   - *Duplicate rows:* Nhân bản 2 dòng để vi phạm ràng buộc khóa duy nhất.
5. **Idempotent Repair:** Đọc lại trực tiếp từ raw records ban đầu và thực hiện lại pipeline làm sạch, đảm bảo tính chất Idempotent (chạy bao nhiêu lần cũng trả về cùng một kết quả chuẩn sạch).

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương pháp phục hồi dữ liệu khi phát hiện Data Corruption.
- **Phương án đã cân nhắc:**
  1. *Sửa lỗi cục bộ (In-place patching):* Viết code đi tìm các dòng bị null để điền tạm hoặc xóa bỏ các dòng bị lỗi.
  2. *Tái tạo từ bản sao lưu thô (Rebuild from Raw Preservation):* Nạp lại từ `data/raw/crossref_records.json` và tái thực thi toàn bộ luồng Transformation.
- **Phương án đã chọn:** Phương án 2 (Rebuild from Raw).
- **Lý do:** In-place patching dễ gây sai lệch logic, không thể phục hồi các trường bị xóa trắng nếu không có bản gốc. Rebuild from Raw đảm bảo tính toàn vẹn 100% của dữ liệu và tuân thủ nguyên lý Idempotent Pipeline trong Data Engineering.

---

## 6. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end của toàn pipeline.
- [x] Mọi kết luận đều có artifact hoặc metric kiểm chứng.
- [x] Báo cáo không chứa bất kỳ API key, token hay secret nào.

**Họ và tên:** Ngọ Doãn Ngọc  
**Ngày xác nhận:** 2026-09-25  
