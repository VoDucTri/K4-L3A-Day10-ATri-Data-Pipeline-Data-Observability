# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | **Đỗ Hoàng Nam Khánh** |
| MSSV | **2A202602423** |
| Khóa/Lớp | K4 |
| Tên nhóm | Nhóm ATri - Day 10 |
| Vai trò chính | **Pipeline Lead & RAG Specialist** |
| Repository | https://github.com/VoDucTri/K4-L3A-Day10-ATri-Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-09-25 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Configuration & Utils | `core/config.py`, `core/utils.py` | Biến môi trường `.env`, cấu hình hệ thống | Object `Settings` và cấu trúc đường dẫn `Paths` | Hoàn thành |
| Vector Index & Retrieval | `src/retrieval/index.py`<br>`LocalEmbeddingIndex` | DataFrame sạch / lỗi, model embedding | ChromaDB collections (`baseline`, `corrupted`, `repaired`) | Hoàn thành |
| Baseline Pipeline Orchestration | `src/pipelines/phase1.py` | Module Ingestion, Cleaning, Retrieval, Evaluation | Luồng chạy Phase 1 hoàn chỉnh, artifact Baseline | Hoàn thành |
| Corruption & Repair Orchestration | `src/pipelines/corruption_flow.py` | Corruption suite, Repair function, Evaluator | Luồng chạy Pha 2 hoàn chỉnh, artifact 3 trạng thái | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Tích hợp Quality Gate vào pipeline | Võ Đức Trí (`src/observability/quality.py`) | Đảm bảo quality checks được gọi đúng lúc trước khi index vector |
| Thử nghiệm cơ chế Repair | Ngọ Doãn Ngọc (`src/ingestion/corruption.py`) | Kết nối hàm `repair_clean_dataframe` vào luồng so sánh 3 trạng thái |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Xây dựng cấu hình hệ thống | `core/config.py` | Tự động tải `.env`, quản lý toàn bộ đường dẫn data artifacts | Lệnh nạp `load_settings()` chạy thành công |
| Nạp và tìm kiếm ngữ nghĩa ChromaDB | `src/retrieval/index.py` | 3 collection vector độc lập, mô hình `all-MiniLM-L6-v2` | Khởi tạo thành công 24 vector, semantic search chính xác |
| Điều phối luồng Baseline Pha 1 | `script/run_phase1.py` | Chạy một lệnh hoàn tất toàn bộ chuỗi mắt xích Baseline | Exit code 0, sinh đủ `phase1_report.md` |
| Điều phối luồng Corruption & Repair | `script/run_corruption_flow.py` | Chạy thông suốt luồng tiêm lỗi $\rightarrow$ đo lường $\rightarrow$ sửa chữa | Exit code 0, sinh đủ `corruption_report.md` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Để hệ thống RAG hoạt động ổn định và có thể so sánh định lượng chính xác giữa các trạng thái dữ liệu (Sạch vs Lỗi vs Sau Phục Hồi), cần phải có một kiến trúc điều phối mạch lạc, cô lập các không gian vector độc lập và đảm bảo pipeline có thể chạy lặp lại an toàn.

### Cách triển khai
1. **Thiết kế Cấu hình tập trung (`core/config.py`):** Tập trung toàn bộ thông số (tên model, top_k, threshold ngày, provider) và đường dẫn dữ liệu vào một dataclass bất biến (`Settings`, `Paths`), tránh hardcode đường dẫn tuyệt đối.
2. **Cô lập Vector Collections:** Thay vì ghi đè lên collection hiện có, hệ thống khởi tạo 3 collection riêng biệt trong ChromaDB:
   - `papers-baseline`: Chứa vector nhúng từ dữ liệu sạch ban đầu.
   - `papers-corrupted`: Chứa vector nhúng từ dữ liệu sau khi bị tiêm lỗi.
   - `papers-repaired`: Chứa vector nhúng sau khi được phục hồi an toàn.
3. **Mô hình nhúng nhẹ và tốc độ cao:** Sử dụng mô hình `sentence-transformers/all-MiniLM-L6-v2` kết hợp chuẩn hóa vector cosine distance, đảm bảo tốc độ nhúng nhanh và độ chính xác ngữ nghĩa cao.
4. **Orchestration End-to-End:** Viết các hàm điều phối `main()` trong `phase1.py` và `corruption_flow.py` liên kết mượt mà từ khâu nạp raw, clean, check quality, index vector, evaluate đến xuất báo cáo Markdown.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn cách tổ chức lưu trữ Vector Database khi thực hiện thử nghiệm Corruption và Repair.
- **Phương án đã cân nhắc:**
  1. *Dùng chung 1 collection:* Ghi đè hoặc xóa sạch collection cũ mỗi khi chuyển pha.
  2. *Tách biệt 3 collections độc lập:* Tạo 3 collection song song (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
- **Phương án đã chọn:** Phương án 2 (Tách biệt 3 collections).
- **Lý do:** Giúp bảo toàn trạng thái vector của từng pha, cho phép QA Agent có thể truy vấn chéo và đối chiếu độc lập bất kỳ lúc nào mà không làm mất dữ liệu của pha trước đó.

---

## 6. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end của toàn pipeline.
- [x] Mọi kết luận đều có artifact hoặc metric kiểm chứng.
- [x] Báo cáo không chứa bất kỳ API key, token hay secret nào.

**Họ và tên:** Đỗ Hoàng Nam Khánh  
**Ngày xác nhận:** 2026-09-25  
