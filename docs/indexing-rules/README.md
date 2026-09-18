# ISC Indexing Rules — Compliance MD Set

> Bộ tài liệu compliance nội bộ của ISC, viết dạng **markdown indexing** để **AI Agent** (Claude Code, Cursor, Copilot…) **và** human dev cùng đọc-cùng-áp-dụng. Một entry point duy nhất (`00_INDEX.md`) dispatch sang 6 file rule chi tiết theo loại task.

---

## Mục đích

1. **Single source of truth** cho compliance ISC — branch/commit/MR, naming, API, response/error, timeout, coding convention.
2. **Indexing-first** — không bắt người đọc (hay AI) load hết. Đọc INDEX, match task, chỉ load file detail cần thiết.
3. **Drop-in cho AI workflow** — repo này có thể clone/copy vào dự án bất kỳ; AI Agent (đặc biệt là Claude Code config-harness) auto-load `00_INDEX.md` khi thư mục tồn tại.

---

## Cấu trúc

```
indexing-rules-md/
├── README.md                       ← file này
├── 00_INDEX.md                     ← ENTRY POINT — đọc TRƯỚC mọi file khác
├── 01_MR_Compliance.md             ← branch / commit / MR / self-check trước push
├── 02_Naming_Microservice.md       ← service / DB / table / column / event naming + R-DECISION (SQL vs Mongo)
├── 03_API_Naming.md                ← REST endpoint, path, HTTP method, query, OpenAPI
├── 04_API_Response_and_Error.md    ← response wrapper 4 field, error category, error code catalog
├── 05_API_Timeout.md               ← timeout config, retry budget, cancellation, log
└── 06_Coding_Convention.md         ← coding convention (.NET priority, naming/format/comment)
```

Mỗi file detail có front-matter (`type`, `audience`, `authoritative`, `last_updated`) + danh sách rule có ID dạng `R-<DOMAIN>-<NUMBER>` (vd `R-API-PATH-002`, `R-COMMIT-001`, `R-TIMEOUT-MUST-001`). Mỗi rule có **severity** + **tier** (xem dưới).

---

## Cách indexing hoạt động

### 1. Decision Tree (mục 🎯 trong INDEX)

INDEX chứa bảng dispatch task → file detail. 6 nhánh:

| Nhánh | Task | Load file |
|---|---|---|
| A | Git / branch / commit / MR | `01_MR_Compliance.md` |
| B | Kiến trúc / data model / DB | `02_Naming_Microservice.md` |
| C | API design / endpoint | `03_API_Naming.md` |
| D | Code response / error handling | `04_API_Response_and_Error.md` |
| E | I/O call / timeout / retry | `05_API_Timeout.md` |
| F | Code style / naming / format | `06_Coding_Convention.md` |

**Một task có thể match nhiều nhánh.** Ví dụ: "tạo endpoint POST trả về list users" → load A (commit) + C (path/method) + D (response wrapper).

### 2. BLOCKER table

INDEX có bảng "BLOCKER tuyệt đối" — danh sách rule ID mà **vi phạm = không được generate output**. Đây là single source of truth cho cảnh báo nghiêm trọng. AI Agent block ngay khi detect; human dev block ngay khi review.

### 3. Cross-cutting rules

Có những rule áp dụng xuyên file (vd: field naming convention, `trace_id` requirement, UUID làm ID, AI Disclosure tag). INDEX gom thành 4 bảng cross-cutting để tra nhanh không phải mở 5 file.

### 4. Conflict resolution

Khi 2 rule mâu thuẫn → INDEX có thứ tự ưu tiên:
1. BLOCKER thắng REQUIRED thắng GOOD_PRACTICE
2. Rule cụ thể thắng rule chung
3. Không rõ → BLOCK, hỏi human

---

## Severity & Tier (cross-cutting, định nghĩa trong INDEX)

### Severity — mức vi phạm

| Mức | Hành xử |
|---|---|
| **BLOCKER** | Tuyệt đối không generate output vi phạm. Block ngay, báo human. |
| **REQUIRED** | Cảnh báo, xin confirm trước khi tiếp tục. |
| **GOOD_PRACTICE** | Note trong commit message, không block. |

### Tier — tầng kiểm tra

| Tier | Ý nghĩa |
|---|---|
| **AUTO_GATE** | CI/GitLab tự enforce. Code đúng để pipeline pass. |
| **DEV_SELF_CHECK** | Dev (hoặc AI đóng vai dev) verify trước MR. |
| **REVIEWER_VERIFY** | Human reviewer kiểm. Code đúng để giảm gánh nặng review. |

---

## Cách dùng — 3 mô hình tích hợp

### Mô hình 1: Tích hợp với Claude Code config-harness *(recommended cho team dùng AI)*

Repo `config-harness-for-claude-code` có pipeline 6-phase đã được wire sẵn để auto-load INDEX.

**Setup**:
```bash
# Clone config-harness vào project của bạn (hoặc dùng template)
git clone git@git.fpt.net:isc/isc-internal-standard/config-harness-for-claude-code.git my-project-claude-config

# Clone bộ rule này vào internal_rules/
cd my-project-claude-config/core/docs/ai/
git clone git@git.fpt.net:isc/isc-internal-standard/indexing-rules-md.git internal_rules
```

**Khi mở Claude Code**, pipeline tự:
1. Phase 0 step 4 phát hiện `internal_rules/00_INDEX.md` tồn tại → load TRƯỚC mọi rule khác.
2. Phase 0 step 5 dispatch theo Decision Tree (vd: "code change" → load thêm `06_Coding_Convention.md`).
3. Phase 1 cite source bắt buộc kèm rule ID khi áp dụng compliance (vd: `Per internal_rules/03_API_Naming.md#R-API-PATH-002`).
4. Phase 3 step 6 chạy compliance check đối chiếu BLOCKER table.
5. Hard Stops point sang BLOCKER table — vi phạm = stop, hỏi human.

→ Không phải config gì thêm. Drop dir vào, pipeline chạy.

### Mô hình 2: Reference cho human dev (không AI)

Đọc trực tiếp ở GitLab UI hoặc clone về local. Workflow:

1. Bookmark `00_INDEX.md` — entry point.
2. Khi gặp task: dùng Decision Tree (mục 🎯) match → mở file detail.
3. Khi viết MR description / commit / PR title: tham khảo `01_MR_Compliance.md`.
4. Khi 2 rule có vẻ mâu thuẫn: tra Conflict resolution (mục ⚖️) trong INDEX.

→ Không cần tool đặc biệt. Chỉ là tài liệu chuẩn.

### Mô hình 3: Cấp cho AI tool khác (Cursor, Copilot, ChatGPT…)

Bộ rule này không phụ thuộc framework. Chỉ cần:

1. Cung cấp đường dẫn / nội dung `00_INDEX.md` cho AI ngay đầu session.
2. Yêu cầu AI tuân thủ "Hành vi load tài liệu" (mục 📥 trong INDEX): luôn load INDEX trước, match Decision Tree, chỉ load file detail cần.
3. Nhắc AI cite rule ID khi reference (vd `R-API-PATH-002`).

Mẫu system prompt tham khảo:

```
Bạn là AI Agent thực hiện task code generation. Trước mọi task:
1. Đọc 00_INDEX.md (entry point compliance).
2. Match task vào Decision Tree A–F.
3. Load file detail tương ứng — chỉ load file cần.
4. Cite rule ID khi áp dụng (vd: "Per R-API-PATH-002, dùng kebab-case").
5. Vi phạm BLOCKER table → STOP, báo human, KHÔNG tự quyết.
6. Conflict 2 rule → tra Conflict resolution, không tự quyết.
```

---

## Cách thêm / sửa rule

### Thêm rule mới vào file detail có sẵn

1. Tìm file đúng domain (`01`–`06`).
2. Thêm rule với ID format `R-<DOMAIN>-<NUMBER>` — đánh số tiếp.
3. Bắt buộc kèm:
   - **Severity** (BLOCKER / REQUIRED / GOOD_PRACTICE)
   - **Tier** (AUTO_GATE / DEV_SELF_CHECK / REVIEWER_VERIFY)
   - Mô tả ngắn + ví dụ vi phạm + ví dụ đúng
4. Nếu rule là BLOCKER → **bắt buộc** cập nhật bảng BLOCKER trong `00_INDEX.md`.
5. Update field `last_updated` ở front-matter file đó VÀ ở `00_INDEX.md`.

### Thêm domain mới (file mới)

1. Tạo file `0N_<Domain>.md` với front-matter và cấu trúc giống các file có sẵn.
2. Update `00_INDEX.md`:
   - Mục 📚 file tree
   - Source-mapping table
   - Decision Tree (mục 🎯) — thêm nhánh mới
   - Cross-cutting rules — nếu domain mới đụng cross-cutting đã có
3. Thông báo các team consumer (ai đang dùng repo này — config-harness, projects khác).

### Khi rule conflict

1. Xác định severity của 2 rule.
2. Severity cao thắng. Cùng severity → rule cụ thể thắng rule chung.
3. Vẫn không rõ → mở MR thảo luận, update mục ⚖️ Conflict resolution của INDEX với case mới.

---

## Versioning

- **Mỗi file detail có owner** (xem front-matter / git blame). Owner approve mọi MR đụng file đó.
- **Conventional Commits** áp dụng (vd `feat(03_api_naming): add R-API-PATH-005`, `fix(00_index): correct BLOCKER row`).
- **Breaking change** (đổi severity của rule có sẵn, xóa rule, đổi semantic) → bump major trong commit message + thông báo consumer.

---

## Liên quan

- **Config-harness Claude Code**: https://git.fpt.net/isc/isc-internal-standard/config-harness-for-claude-code
- **Vấn đề / đề xuất rule mới**: tạo Issue trên repo này.

---

*ISC Internal Standard — Indexing Rules MD set. Single source of truth cho compliance, dùng cho cả AI và human.*
