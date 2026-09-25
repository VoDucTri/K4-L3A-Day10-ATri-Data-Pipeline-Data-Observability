# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | **K4 - L3A** |
| Tên nhóm | **Nhóm ATri - Day 10** |
| Repository | https://github.com/VoDucTri/K4-L3A-Day10-ATri-Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-09-25 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | **Võ Đức Trí** *(Trưởng nhóm)* | 2A202602603 | **Observability & Evaluation Lead** | `src/observability/quality.py`, `src/evaluation/testset.py`, `src/observability/reporting.py`, quản trị Git & review merge |
| 2 | **Ngọ Doãn Ngọc** | 2A202602635 | **Data Foundation & Recovery Owner** | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/ingestion/corruption.py`, cơ chế Idempotent Repair |
| 3 | **Đỗ Hoàng Nam Khánh** | 2A202602423 | **Pipeline Lead & RAG Specialist** | `core/config.py`, `src/retrieval/index.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |

---

## 2. Tóm tắt kết quả

Nhóm đã xây dựng thành công Data Pipeline hoàn chỉnh 7 tầng cho hệ thống RAG Agent học thuật, tích hợp Data Observability theo chuẩn mới Great Expectations 1.x (chạy RAM `ephemeral`) và giám sát Freshness SLA (ngưỡng 180 ngày). 

Ở pha Baseline, pipeline đã thu thập 24 bài báo khoa học từ Crossref API, làm sạch dữ liệu, vượt qua 100% Quality Gate và nạp vào ChromaDB với mô hình `all-MiniLM-L6-v2`, đạt Retrieval Hit Rate tuyệt đối 1.0000 và Token F1 đạt 0.7500. 

Ở pha thử nghiệm tiêm lỗi, nhóm đã kích hoạt 6 kịch bản Synthetic Corruption. Kết quả chứng minh hiện tượng **Silent Failure**: dù hệ thống không hề văng Exception đỏ, Data Quality Gate và Freshness SLA lập tức gióng chuông cảnh báo (`success=False`, 10/24 bài bị stale), đồng thời Retrieval Hit Rate sụt giảm nghiêm trọng xuống 0.7500 và Token F1 giảm xuống 0.5106. 

Khi kích hoạt cơ chế Idempotent Repair, hệ thống đã tự động tái tạo dữ liệu sạch từ bản sao lưu thô ban đầu (Raw Preservation), đưa toàn bộ chỉ số Hit Rate (1.0000) và Token F1 (0.7500) phục hồi nguyên vẹn về mức chuẩn ban đầu. Toàn bộ mã nguồn đã xóa sạch TODO(student), thực thi một mạch trơn tru không lỗi.

---

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Nguồn Crossref REST API (hoặc Snapshot Offline data/raw/)
    ├── 1. Kéo dữ liệu & Lưu bản gốc (Raw Preservation) -> data/raw/crossref_records.json
    ├── 2. Làm sạch & Chuẩn hóa (Transformation)        -> data/clean/papers_clean.csv
    ├── 3. Trạm kiểm soát chất lượng (Quality Gate)     -> Great Expectations 1.x & Freshness SLA
    ├── 4. Nhúng ngữ nghĩa & Lưu Vector (Index)         -> all-MiniLM-L6-v2 + ChromaDB
    ├── 5. Đánh giá chất lượng RAG (Benchmark)          -> Hit Rate, Token F1, LLM Judge Score
    ├── 6. Thử thách tiêm độc tố dữ liệu (Corruption)   -> Giả lập 6 lỗi dữ liệu thực tế
    └── 7. Phục hồi an toàn & Đối chiếu (Repair)        -> Tái tạo từ Raw & Báo cáo 3 trạng thái
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref API / Snapshot | Fetch HTTP với timeout/retry, fallback đọc file thô | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Ngọ Doãn Ngọc |
| Cleaning | Raw records JSON | Làm sạch HTML/JATS XML, tính `age_days`, khử trùng lặp | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Ngọ Doãn Ngọc |
| Embedding & Index | Cleaned DataFrame | Nhúng ngữ nghĩa `all-MiniLM-L6-v2`, nạp Chroma collection | `data/chroma/`, `data/embeddings/papers_embeddings.json` | Đỗ Hoàng Nam Khánh |
| Evaluation | Test set JSON & Index | Đo lường Retrieval Hit Rate, Token F1, LLM Judge Score | `data/results/baseline_metrics.json` | Võ Đức Trí |
| Observability | Cleaned / Corrupted DataFrame | Chốt kiểm dịch Great Expectations 1.x & Freshness SLA | `data/quality/*_quality_report.json`, `freshness_report.json` | Võ Đức Trí |
| Corruption & Repair | Clean DataFrame & Raw records | Tiêm 6 kịch bản lỗi, tự phục hồi từ raw data | `data/results/corruption_log.json`, `repaired_clean.csv` | Ngọ Doãn Ngọc |
| Orchestration | Cấu hình Settings | Điều phối toàn luồng Phase 1 và Corruption Flow | `script/run_phase1.py`, `script/run_corruption_flow.py` | Đỗ Hoàng Nam Khánh |

---

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` | `gemini` (hoặc `mock` cho offline) |
| `LLM_MODEL` | `gemini-2.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày |
| Random seed, nếu có | 42 |

### Lệnh chạy tái hiện

Kích hoạt môi trường và chạy 2 lệnh chính thức:

```powershell
# Chạy Pha 1 (Baseline Pipeline)
python script/run_phase1.py

# Chạy Pha 2 (Corruption, Repair & Comparison Flow)
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| --- | --- | --- | --- |
| Baseline pipeline | Thành công (100%) | 2026-09-25 16:12 | `data/reports/phase1_report.md`, Exit code 0 |
| Corruption flow | Thành công (100%) | 2026-09-25 16:16 | `data/reports/corruption_report.md`, Exit code 0 |

---

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | Crossref REST API công khai (`https://api.crossref.org/works`) |
| Query/filter | `query=agentic retrieval augmented generation large language model`, `filter=from-pub-date:...,has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-09-25 |
| Số record nhận được | 24 bài báo |
| Cơ chế retry/backoff | Timeout 15s, tự động fallback đọc snapshot có sẵn `data/raw/crossref_response.json` khi dính 429 hoặc mất mạng |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | `str` | Có | Định danh DOI chuẩn hóa | Bỏ qua bản ghi nếu không có DOI |
| `title` | `str` | Có | Tiêu đề bài báo | Chuẩn hóa khoảng trắng thừa |
| `summary` | `str` | Có | Tóm tắt bài báo | Loại bỏ toàn bộ thẻ `<jats:p>`, `</jats:p>` |
| `authors` | `list[str]` | Có | Danh sách tên tác giả | Ghép nối thành chuỗi `authors_joined` |
| `published` | `str` | Có | Ngày xuất bản ISO 8601 | Parse định dạng `YYYY-MM-DD` |
| `age_days` | `int` | Có | Số ngày tuổi từ ngày công bố | Tính toán: `(current_date - published).days` |
| `text_for_embedding` | `str` | Có | Nội dung tổng hợp 5 phần | Ghép Title, Authors, Published, Categories, Summary |

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Số record bị tác động | Cách xác minh |
| --- | --- | ---: | --- |
| Loại bỏ thẻ rác HTML/XML trong tóm tắt | Validity & Accuracy | 24 | Regex clean thẻ `<jats:p>` |
| Khử trùng lặp bản ghi theo DOI | Uniqueness | 0 | `df.drop_duplicates(subset=['paper_id'])` |
| Chuẩn hóa định dạng ngày tháng | Consistency | 24 | ISO 8601 parser |
| Sinh cột `text_for_embedding` | Completeness | 24 | Đủ 5 thành phần cấu trúc chuẩn |

---

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 32 câu hỏi benchmark cố định |
| Các `question_type` | `summary`, `authors`, `date`, `category`, `multi_hop` |
| Ground-truth document ID | Trích xuất trực tiếp DOI của tài liệu nguồn |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection | ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval `top_k` | 4 |
| LLM provider/model | `gemini-2.5-flash` (hoặc `mock` deterministic fallback) |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

*Lý do giữ nguyên test set:* Đảm bảo tính nhất quán của biến số nghiên cứu thực nghiệm. Việc cố định bài test giúp mọi biến thiên của các chỉ số (Hit Rate, Token F1) hoàn toàn phản ánh tác động của chất lượng dữ liệu.

---

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| Raw response/records | `data/raw/crossref_records.json` | Có | Đầy đủ 24 bản ghi gốc |
| Cleaned dataset | `data/clean/papers_clean.csv` | Có | 24 dòng sạch hoàn chỉnh |
| Embedding manifest/index | `data/embeddings/papers_embeddings.json` | Có | 24 vector đã nạp |
| Evaluation set | `data/eval/test_set.json` | Có | 32 câu hỏi benchmark |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Hit Rate: 1.0000, F1: 0.7500 |
| Quality/freshness | `data/quality/baseline_quality_report.json` | Có | Great Expectations passed |
| Baseline report | `data/reports/phase1_report.md` | Có | Markdown report chi tiết |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | **1.0000** | 100% câu hỏi kéo đúng tài liệu tham chiếu chuẩn |
| `mean_token_f1` | **0.7500** | Độ trùng khớp từ vựng đạt mức cao xuất sắc |
| `judge_accuracy` | **0.7500** | Tỷ lệ câu trả lời đúng bản chất ngữ nghĩa |
| `mean_judge_score` | **4.0** | Điểm số đánh giá chất lượng trung bình (thang 1 - 5) |

---

## 8. Data quality và freshness

### Quality checks (Great Expectations 1.x)

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| --- | --- | --- | --- | --- |
| `ExpectTableRowCountToBeBetween` | Completeness | [5, 5000] | Pass (24 dòng) | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` | Completeness | Not null (`paper_id`, `title`, `text`) | Pass (0 null) | `baseline_quality_report.json` |
| `ExpectColumnValuesToBeUnique` | Uniqueness | Duy nhất `paper_id` | Pass (100% unique) | `baseline_quality_report.json` |
| `ExpectColumnValueLengthsToBeBetween` | Validity | `summary` length >= 30 | Pass (min >= 30) | `baseline_quality_report.json` |

### Freshness SLA

| Thuộc tính | Giá trị |
| --- | --- |
| Freshness được đo tại | `data/clean/papers_clean.csv` qua trường `age_days` |
| Timestamp mới nhất | Ngày chạy thực nghiệm gần nhất (2026-09-25) |
| Ngưỡng freshness SLA | Tỷ lệ bài báo cũ (`age_days > 180`) không vượt quá 25% |
| Trạng thái baseline | **Fresh (Đạt chuẩn SLA)** |
| Lý do | 0/24 bài báo bị cũ quá 180 ngày tại thời điểm baseline |

---

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| --- | --- | ---: | --- | --- | --- |
| 1. Drop latest records | Bỏ rơi các bài báo mới nhất | 4 | Freshness SLA cảnh báo | Thiếu dữ liệu tươi | Nạp lại toàn bộ từ raw snapshot |
| 2. Blank summary | Xóa trắng tóm tắt một số dòng | 4 | GX `summary length` báo lỗi | Mất thông tin tóm tắt | Tái tạo lại từ raw records gốc |
| 3. Inject text noise | Chèn ký tự rác vô nghĩa | 4 | Vector search bị lệch | Giảm độ chính xác semantic | Làm sạch lại từ bản raw |
| 4. Truncate title | Cắt ngắn tiêu đề bài báo < 10 ký tự | 4 | GX validation cảnh báo | Nhiễu tiêu đề | Khôi phục tiêu đề gốc |
| 5. Stale date | Đổi ngày công bố về 5 năm trước | 10 | Freshness SLA kích hoạt | Tỷ lệ stale > 25% | Lấy lại timestamp gốc từ raw |
| 6. Duplicate rows | Nhân bản dòng để trùng lặp DOI | 2 | GX `paper_id unique` báo lỗi | Trùng lặp index vector | Khử trùng lặp theo `paper_id` |

- **Corruption log:** Được lưu trữ đầy đủ tại `data/results/corruption_log.json`.
- **Cơ chế Idempotent Repair:** Hệ thống không vá lỗi cục bộ bằng tay, mà kích hoạt quy trình tái nạp từ nguồn dữ liệu thô ban đầu (`crossref_records.json`), chạy lại toàn bộ quy trình Cleaning và Quality Gate. Dù chạy lại bao nhiêu lần, kết quả luôn nhất quán và chuẩn sạch.

---

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.7500 | 1.0000 | -25.0% | +25.0% | Phục hồi hoàn toàn về mức 1.0000 |
| `mean_token_f1` | 0.7500 | 0.5106 | 0.7500 | -23.94% | +23.94% | Phục hồi về mức chuẩn 0.7500 |
| `judge_accuracy` | 0.7500 | 0.5000 | 0.7500 | -25.0% | +25.0% | Phục hồi độ chính xác câu trả lời |
| `mean_judge_score` | 4.0 | 3.0 | 4.0 | -1.0 | +1.0 | Điểm đánh giá trở lại mức Tốt |
| Quality checks pass/fail | **PASSED** | **FAILED** | **PASSED** | Báo động đỏ | Phục hồi xanh | Bắt đúng lỗi schema & unique DOI |
| Freshness status | **PASSED** | **FAILED** | **PASSED** | 10/24 bài stale | 0 stale | Phát hiện chính xác vi phạm SLA |

### Hai kết luận nhân quả thực nghiệm:
1. **Tác động của dữ liệu bẩn (Corruption):**  
   Khi 6 loại lỗi dữ liệu được tiêm vào $\rightarrow$ Data Quality Gate báo `FAILED` và Freshness báo vi phạm (10/24 bài stale) $\rightarrow$ Retrieval Hit Rate sụt giảm sâu từ 1.0000 xuống 0.7500 và Token F1 giảm còn 0.5106. Đây là bằng chứng thực nghiệm rõ ràng nhất cho hiện tượng **Silent Failure**.
2. **Hiệu quả của phục hồi an toàn (Repair):**  
   Khi kích hoạt cơ chế Idempotent Repair tái tạo từ raw preservation $\rightarrow$ Quality Gate và Freshness SLA đồng thời chuyển sang trạng thái `PASSED` $\rightarrow$ Toàn bộ chỉ số Retrieval Hit Rate và Token F1 phục hồi 100% về mức ban đầu.

---

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Khi chạy lệnh kiểm tra trên Windows PowerShell mặc định, console báo lỗi `UnicodeEncodeError: 'charmap' codec can't encode characters in position 6-7: character maps to <undefined>`.
- **Nguyên nhân:** PowerShell trên Windows sử dụng bảng mã mặc định `cp1252`, không tương thích với các chuỗi log tiếng Việt có dấu (`Môi trường sẵn sàng`).
- **Cách xử lý:** Thiết lập biến môi trường `$env:PYTHONIOENCODING = "utf-8"` trước khi thực thi script, đồng thời sử dụng đường dẫn ngắn chuẩn 8.3 (`73EC~1`) để tránh ký tự đặc biệt trong đường dẫn `Documents`.
- **Cách xác minh:** Toàn bộ pipeline chạy mượt mà, log in đầy đủ tiếng Việt có dấu, exit code 0.

---

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| Tập dữ liệu thử nghiệm ở quy mô 24 bài báo | Chưa kiểm chứng được hiệu năng ở quy mô hàng triệu vector | Mở rộng benchmark lên 10.000 bài báo và đo lường latency của HNSW index |
| Phục hồi hiện tại dựa trên local raw snapshot | Chưa có cơ chế auto-healing tức thời khi API bị đứt kết nối | Tích hợp webhook tự động phát hiện vi phạm và kích hoạt rollback pipeline |

---

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác (`Nhóm ATri - Day 10`).
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp (`python script/run_phase1.py` & `python script/run_corruption_flow.py`).
- [x] Baseline, corrupted và repaired dùng cùng evaluation set cố định.
- [x] Bảng metrics khớp chính xác với các file JSON trong `data/results/`.
- [x] Quality/freshness conclusions khớp 100% với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được đầy đủ.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng trong `report/`.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay commit history.
