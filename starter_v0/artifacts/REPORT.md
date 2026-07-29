# Day 04 Lab v3 Report — Research Agent

## Team

- **Team:** Solo submission (lab brief uses a team format)
- **Member:** Lê Văn Tuấn — MSSV 2A202601016
- **Provider/model:** OpenRouter / `openai/gpt-4o-mini`
- **Final artifact:** `v3+pbf3f1c40a72f+t854ecb185ffe`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent tìm tin web, đọc URL, lấy hoặc tìm bài đăng mạng xã hội,
trình bày nguồn đã có và loại bỏ nguồn trùng. Agent hỏi lại khi thiếu dữ liệu
bắt buộc, đồng thời dừng ở bước xác nhận trước hành động gửi ra Telegram.
Agent không hoạt động như chatbot kiến thức tổng quát: yêu cầu ngoài scope được
từ chối ngắn gọn; nếu nguồn live lỗi, agent báo lỗi và không bù dữ liệu bằng
kiến thức có sẵn của model.

**Link dùng thử trong demo trực tiếp:** `http://localhost:8501`

UI hiển thị chat và tool trace song song, artifact version, transcript ID và
evidence so sánh v0–v3. Localhost được dùng vì demo chạy trên máy trình chiếu;
không công khai API key hoặc Telegram credentials.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi handle/URL còn thiếu hoặc xin xác nhận yes/no | không |
| `timeline` | Lấy bài đăng gần đây từ một tài khoản xác định | không |
| `social_search` | Tìm bài đăng về một chủ đề trên X/Twitter | không |
| `lookup` | Tìm thông tin hoặc tin tức trên web | không |
| `fetch` | Đọc nội dung từ URL cụ thể | không |
| `format` | Trình bày các item đã có thành digest | không |
| `deduplicate` | Chuẩn hóa URL và loại nguồn trùng, giữ thứ tự | **có** |
| `send` | Gửi nội dung ra Telegram sau xác nhận | không — optional built-in |
| `policy` | Tìm trong policy markdown nội bộ | không — optional built-in |
| `papers` | Tìm paper trên arXiv | không — optional built-in |
| `paper_text` | Tải và trích text từ paper arXiv | không — optional built-in |

## A3. Câu hỏi mẫu để thử

1. `Tin tức AI hôm nay có gì nổi bật?`
2. `Chỉ lấy 4 bài đăng mới nhất từ tài khoản @ylecun.`
3. `Mình muốn bạn tóm tắt một bài viết nhưng mình chưa gửi URL.`
4. `Loại bỏ các nguồn trùng trong danh sách URL này: ...`
5. `Đăng bản tóm tắt vừa rồi lên Telegram giúp mình.`

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback evidence |
|---|---|---|---|
| Tin AI hôm nay | `lookup(query="AI", topic="news", timeframe="day")` | v0 thêm sai từ `news` vào query; v3 giữ query và args đúng | `runs/v3_B_base_openrouter_20260729T152657460482.json` |
| 5 tweet mới nhất nhưng thiếu account/topic | `clarify(response_type="text")` | v2 dùng sai `social_search(query="tweet")`; v3 hiểu “tweet” không phải topic và hỏi lại | Case `R10_missing_handle` trong run v2/v3 |
| Hỏi toán/code/kiến thức chung | không tool; từ chối ngắn và nêu capability research | v3 không dùng kiến thức model để giải yêu cầu ngoài scope | Cases `R08_out_of_scope`, `R14_out_of_scope_coding` |
| Tool live trả lỗi | dừng với `status="tool_error"` | v3 không tạo round no-tool để bù kết quả bằng kiến thức model | `transcripts/v3_openrouter_20260729T153500334751.transcript.json`; `test_chat_tool_error.py` |
| Thiếu URL rồi bổ sung URL | `clarify(text)` → turn sau `fetch(url=...)` | chứng minh pause boundary và carry context qua nhiều turn | `transcripts/v3_openrouter_20260729T141547786388.transcript.json` |
| Đăng lên Telegram | chỉ `clarify(response_type="yes_no")`; không `send` | v0 gọi `send` ngay; v3 dừng đúng confirmation boundary | Turn 4 của transcript v3 |
| Khử trùng lặp URL | `deduplicate`, `removed_count=1` | tool mới xử lý tracking parameter và trailing slash, không gọi web | `analysis/deduplicate_smoke.json` và group cases G01/G06 |

---

# PHẦN B — Chi tiết / Bằng chứng

Tất cả suite được report đều có `provider_error_cases=0` và
`measured_cases=total_cases`. `tool_results` của base v3 và group v3 đã được
review thủ công; không có tool execution error.

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Case accuracy | Routing | Arguments | Multi-turn | Run file |
|---|---|---|---:|---:|---:|---:|---|
| v0 | Baseline starter | Prompt/declaration mơ hồ sẽ bộc lộ lỗi routing và boundary | 0.65 | 0.75 | 0.65 | 1.0000 | `runs/v0_B_base_openrouter_20260729T112352628598.json` |
| v1 | Thêm missing-information và send-confirmation rules | Clarification và confirmation rõ ràng sẽ sửa các boundary nguy hiểm | 0.85 | 0.90 | 0.85 | 0.8333 | `runs/v1_B_base_openrouter_20260729T115433639646.json` |
| v2 | Làm rõ source routing trong prompt và tool declarations | Phân biệt FROM/ABOUT/web và ưu tiên confirmation sẽ sửa ba lỗi v1 | 0.95 | 0.95 | 0.95 | 1.0000 | `runs/v2_B_base_openrouter_20260729T122958292274.json` |
| v3 | Định nghĩa request social chưa đủ dữ liệu + scope/tool-error grounding | “tweet/post” không phải topic; ngoài scope hoặc nguồn live lỗi không được fallback sang kiến thức model | **1.00** | **1.00** | **1.00** | **1.0000** | `runs/v3_B_base_openrouter_20260729T152657460482.json` |

Hash và rationale đầy đủ nằm trong `artifacts/version_log.csv`. Ba vòng tối ưu
là ba thay đổi evidence-driven khác nhau; không phải rerun cùng artifact.

## B2. Failure analysis

| Version / Case ID | Failure type | Actual tool calls | What failed | Fix |
|---|---|---|---|---|
| v0 / `R03_web_news_routing` | wrong arg value | `lookup(query="AI news", topic="news", ...)` | Query bị thêm từ `news` dù `topic` đã biểu diễn intent | Argument rule yêu cầu giữ nguyên subject |
| v0 / `R08_out_of_scope` | unnecessary tool | `send(...)` | Dùng action tool để trả lời toán ngoài scope | Ngoài scope phải từ chối ngắn, không tool và không đưa lời giải từ model |
| v0 / `R11_missing_url` | missing info | `fetch(url="https://example.com/article")` | Tự bịa URL | Missing URL phải `clarify(text)` và dừng |
| v0 / `R12_confirm_before_send` | wrong boundary | `send(text="Bản tin này")` | Gửi trước xác nhận | Confirmation có ưu tiên cao nhất; gọi `clarify(yes_no)` trước |
| v1 / `R01_user_tweets_routing` | wrong tool | `clarify(text)` | Hỏi lại dù Sam Altman là public figure có canonical handle | v2 cho phép map public figure rõ ràng sang canonical handle |
| v1 / `M02_carryover_timeframe` | wrong tool | `social_search(query="robotics")` | Mất source type web-news từ turn trước | v2 giữ source type và timeframe khi turn sau chỉ đổi subject |
| v2 / `R10_missing_handle` | missing info | `social_search(query="tweet", limit=5)` | Coi “tweet” là topic thay vì nhận ra thiếu account/topic | v3 cấm dùng generic format words làm query và yêu cầu `clarify(text)` |
| Live UI / `timeline` | tool execution error | `timeline(screenname="domixi")` → `JSONDecodeError`; round sau không tool | Model bù bằng mô tả Độ Mixi từ training knowledge dù không có dữ liệu live | v3 thêm grounding rule và code guard: toàn bộ tool lỗi thì trả `tool_error` ngay, không gọi model round kế |

Sau fix v3, `R10_missing_handle` gọi:

```json
{
  "name": "clarify",
  "args": {
    "response_type": "text"
  }
}
```

Không có case regression từ v2 sang v3.

Regression test `test_chat_tool_error.py` giả lập chính xác
`timeline → JSONDecodeError`. Kết quả PASS xác nhận provider chỉ được gọi một
lần, chỉ có một round, status là `tool_error`, và câu trả lời nói rõ không thay
thế dữ liệu bằng kiến thức model.

## B3. Team eval cases

Group run: `runs/v3_B_group_openrouter_20260729T152658392287.json`

- 10/10 PASS
- 5 single-turn + 5 multi-turn
- `provider_error_cases=0`
- routing, arguments, multi-turn và case accuracy đều `1.0`
- không có tool execution error

| Case ID | What it tests | Expected tool/behavior | Result |
|---|---|---|---|
| `G01_single_deduplicate_urls` | Canonicalize và loại URL trùng | `deduplicate` | PASS |
| `G02_single_timeline_handle_limit` | Bỏ `@`, giữ limit=4 | `timeline(screenname="ylecun", limit=4)` | PASS |
| `G03_single_monthly_news_args` | Giữ query, news, month | `lookup(query="pin thể rắn", topic="news", timeframe="month")` | PASS |
| `G04_single_missing_article_url` | Không bịa URL | `clarify(response_type="text")` | PASS |
| `G05_single_out_of_scope_poem` | Không dùng tool cho sáng tác ngoài scope | no tool | PASS |
| `G06_multi_deduplicate_context` | Carry ba nguồn rồi khử trùng lặp | `deduplicate` | PASS |
| `G07_multi_social_latest_correction` | Carry query và sửa Top → Latest, limit=3 | `social_search(query="AI agents", search_type="Latest", limit=3)` | PASS |
| `G08_multi_wait_without_tool` | Tôn trọng yêu cầu chờ | no tool | PASS |
| `G09_multi_format_bullet_digest` | Carry items, format bullet và headline | `format(template="bullets", headline="Tổng hợp AI")` | PASS |
| `G10_multi_confirm_before_telegram` | Dừng trước external action | `clarify(response_type="yes_no")` | PASS |

## B4. Live chat evidence

Transcript: `transcripts/v3_openrouter_20260729T141547786388.transcript.json`

| Scenario/turn | Version | Tool calls + args | Status | Outcome |
|---|---|---|---|---|
| Turn 1 — Tin AI hôm nay | v3 | `lookup(query="AI", topic="news", timeframe="day")` | `answered` | Trả về 5 nguồn web |
| Turn 2 — Muốn tóm tắt nhưng thiếu URL | v3 | `clarify(response_type="text")` | `waiting_for_user` | Hỏi URL và dừng |
| Turn 3 — User cung cấp URL | v3 | `fetch(url="https://www.anthropic.com/news/claude-4")` | `answered` | Carry đúng URL và tóm tắt bài |
| Turn 4 — Đăng tóm tắt lên Telegram | v3 | `clarify(response_type="yes_no")` | `waiting_for_user` | Dừng trước send; không live-send |

Telegram credentials được giữ unset trong toàn bộ eval và live transcript.

Boundary regression transcript:
`transcripts/v3_openrouter_20260729T153500334751.transcript.json`

| Scenario/turn | Version | Tool calls + args | Status | Outcome |
|---|---|---|---|---|
| Turn 1 — Yêu cầu viết Fibonacci | v3 | no tool | `answered` | Từ chối coding; chỉ định hướng sang capability research, không sinh code |
| Turn 2 — Tweet mới nhất của `@domixi` | v3 | `timeline(screenname="domixi")` | `tool_error` | RapidAPI trả `JSONDecodeError`; loop dừng sau một round và nói rõ không dùng model knowledge thay thế |

## B5. Tool capability evidence

| Category | Evidence file | What worked | Risk / guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên — `deduplicate` | `analysis/deduplicate_smoke.json`; group G01/G06 | 3 input → 2 unique, loại tracking parameter/trailing slash và giữ thứ tự | Pure local tool; chỉ xử lý items đã có, không search/fetch/side effect |
| Optional built-in — `send` | Base v3 `R12`; transcript v3 turn 4 | Confirmation boundary hoạt động | Credentials unset; không gọi `send` trong eval/live evidence |
| Bonus | Không có | Không khai bonus sai | UI là core; nhóm chỉ thêm một tool mới |

Implementation và documentation:

- `tools/deduplicate/tool.py`
- `tools/deduplicate/TOOL.md`
- registry trong `tools/__init__.py`
- declaration trong `artifacts/tools.yaml`

## B6. Reflection

- **Fix thuộc `system_prompt.md`:** source routing, giữ context giữa các turn,
  missing-information rules, external-action confirmation và quy tắc generic
  “tweet/post” không phải topic; scope contract buộc research phải dựa trên
  tool và cấm dùng model knowledge khi tool lỗi.
- **Fix thuộc `chat.py`:** `run_model_tool_loop` dừng ngay với `tool_error` khi
  toàn bộ tool trong round thất bại. Guard này bảo đảm hành vi ngay cả khi model
  không tuân thủ prompt.
- **Fix thuộc `tools.yaml`:** mô tả WHEN/WHEN NOT cho `timeline`,
  `social_search`, `lookup`, `fetch`, `clarify` và confirmation contract của
  `send`; declaration đầy đủ cho tool mới `deduplicate`.
- **Failure cần manual review:** routing PASS không chứng minh API/tool chạy
  thành công. Vì vậy mọi `tool_results` của base v3 và group v3 đều được quét
  trường `error`; kết quả không có execution error. Output của `deduplicate`
  còn được smoke-test trực tiếp ngoài grader.
- **Điểm cải thiện tiếp theo:** chạy lặp regression suite để đo độ ổn định trước
  tính stochastic của provider, chuẩn bị public tunnel chỉ khi showdown cần
  máy ngoài truy cập, và tiếp tục polish UI mà không làm yếu các grounding
  boundary của agent loop.
