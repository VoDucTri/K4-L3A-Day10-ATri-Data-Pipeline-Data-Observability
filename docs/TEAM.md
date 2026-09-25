# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `Nhóm ATri - Day 10`
- **Mã Nhóm / Lớp:** `K4-L3-DAY10`
- **Tên Repository Nộp Bài:** `https://github.com/VoDucTri/K4-L3A-Day10-ATri-Data-Pipeline-Data-Observability`

---

## 👥 Danh Sách Thành Viên (Nhóm 3 người)

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|:---:|---|---|---|---|---|
| 1 | **Võ Đức Trí** *(Trưởng nhóm)* | 2A202602603 | voductri744464@gmail.com | **Observability & Evaluation Lead** (`observability/quality.py`, `evaluation/testset.py`, reporting, review & merge code) | `report/2A202602603_VoDucTri.md` |
| 2 | **Ngọ Doãn Ngọc** | 2A202602635 | ngodoanngoc@gmail.com | **Data Foundation & Recovery Owner** (`ingestion/crossref.py`, `ingestion/cleaning.py`, raw data & data repair) | `report/2A202602635_NgoDoanNgoc.md` |
| 3 | **Đỗ Hoàng Nam Khánh** | 2A202602423 | khanhd1205673@gmail.com | **Pipeline Lead & RAG Specialist** (`retrieval/index.py`, embedding model, `pipelines/phase1.py`, `pipelines/corruption_flow.py`) | `report/2A202602423_DoHoangNamKhanh.md` |

---

## 📋 Phân Công Chi Tiết & Đóng Góp Cá Nhân

### 1. Võ Đức Trí (MSSV: 2A202602603)
- **Vai trò:** Trưởng nhóm & Observability & Evaluation Lead.
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập Data Quality Gate tự động theo chuẩn **Great Expectations 1.x** (chạy RAM `ephemeral` với 4 Expectations cốt lõi).
  - Triển khai kiểm tra độ tươi Freshness SLA (`age_days` threshold 180 ngày).
  - Quản lý bộ Benchmark Test Set và thực thi đánh giá các chỉ số: Retrieval Hit Rate, Mean Token F1, LLM Judge Score.
  - Tổng hợp, phân tích hiện tượng Silent Failure và xuất bảng đối chiếu 3 trạng thái trong `data/reports/corruption_report.md`.
  - Quản trị GitHub repository, review code và thực hiện merge các nhánh thành viên vào `main`.
- **Điều học được / Đóng góp chính:**
  - Nắm vững cách thiết lập trạm kiểm soát chất lượng dữ liệu để phát hiện Silent Failure trước khi dữ liệu độc hại lọt vào Vector Store.

### 2. Ngọ Doãn Ngọc (MSSV: 2A202602635)
- **Vai trò:** Data Foundation & Recovery Owner.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng module thu thập Crossref Academic API và cơ chế Offline Snapshot fallback trong `src/ingestion/crossref.py`.
  - Bóc tách, làm sạch dữ liệu, khử trùng lặp và chuẩn hóa trường `text_for_embedding` trong `src/ingestion/cleaning.py`.
  - Xây dựng 6 kịch bản tiêm lỗi dữ liệu thực tế (Synthetic Corruption) trong `src/ingestion/corruption.py`.
  - Thiết kế luồng Idempotent Repair phục hồi toàn vẹn dữ liệu từ snapshot thô ban đầu.
- **Điều học được / Đóng góp chính:**
  - Nắm vững nguyên lý Data Lineage và thiết kế Idempotent Pipeline đảm bảo khả năng tự phục hồi mà không phụ thuộc vào can thiệp thủ công.

### 3. Đỗ Hoàng Nam Khánh (MSSV: 2A202602423)
- **Vai trò:** Pipeline Lead & RAG Specialist.
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập cấu hình hệ thống `core/config.py` và quản lý đường dẫn artifacts `core/utils.py`.
  - Tích hợp mô hình nhúng ngữ nghĩa `sentence-transformers/all-MiniLM-L6-v2` và Vector Store ChromaDB trong `src/retrieval/index.py`.
  - Kết nối luồng thực thi toàn diện trong `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`.
  - Tối ưu hóa Vector Retrieval và tích hợp bộ suy luận đánh giá QA Agent.
- **Điều học được / Đóng góp chính:**
  - Hiểu sâu về kiến trúc luồng dữ liệu 7 tầng cho AI/RAG và phương pháp cô lập các không gian vector độc lập (Baseline vs Corrupted vs Repaired).
