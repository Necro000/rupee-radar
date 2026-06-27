# RupeeRadar — Edge Cases & Corner Cases

This document catalogs edge cases, failure scenarios, and ambiguous inputs for RupeeRadar. It is derived from [architecture.md](./architecture.md) and [implementation-plan.md](./implementation-plan.md) and should guide testing, error handling, and MVP scoping.

**Legend**

| Priority | Meaning |
|----------|---------|
| **P0** | Must handle for MVP; breaks demo or corrupts results if ignored |
| **P1** | Should handle; degrades UX or accuracy noticeably |
| **P2** | Nice to have; document as known limitation if deferred |

---

## 1. Upload & Ingestion

### 1.1 File format & structure

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| ING-01 | Empty file (0 bytes) | Reject with 400: *"File is empty"* | P0 | 1 |
| ING-02 | CSV with headers only, no data rows | Complete with 0 transactions; empty-state guidance on dashboard | P0 | 1, 4 |
| ING-03 | Unsupported extension (`.txt`, `.json`, `.doc`) | Reject with 400 + list of supported formats | P0 | 1 |
| ING-04 | File extension `.csv` but content is not CSV (e.g., binary PDF) | Reject after MIME/content sniff; do not crash parser | P0 | 1 |
| ING-05 | File exceeds size limit (e.g., >10 MB) | Reject with 413 and max size in message | P0 | 1 |
| ING-06 | Very large valid file (5,000+ rows) | Process or cap with warning; pipeline completes within timeout | P1 | 1 |
| ING-07 | CSV with non-UTF-8 encoding (Latin-1, Windows-1252) | Attempt encoding detection; fallback error if unreadable | P1 | 1 |
| ING-08 | CSV with BOM (UTF-8 BOM prefix) | Strip BOM; parse normally | P1 | 1 |
| ING-09 | Multiple sheets in Excel | Auto-select sheet with most transaction-like rows; or prompt user (Phase 6) | P2 | 6 |
| ING-10 | Password-protected Excel/PDF | Reject with clear message: *"Encrypted files not supported"* | P2 | 6 |
| ING-11 | Scanned/image-only PDF (no text layer) | Reject or return 0 rows; suggest CSV export from bank | P2 | 6 |
| ING-12 | PDF with multiple unrelated tables | Extract largest table or bank-specific template; warn if ambiguous | P2 | 6 |

### 1.2 Delimiter & column detection

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| ING-20 | Semicolon-delimited CSV (European export) | Sniff delimiter; parse correctly | P1 | 1 |
| ING-21 | Tab-delimited (TSV) | Sniff delimiter; parse correctly | P1 | 1 |
| ING-22 | Quoted fields containing commas | pandas/CSV parser handles escaped quotes | P0 | 1 |
| ING-23 | Multi-line description inside quoted cell | Preserve as single description; do not split into two transactions | P1 | 1 |
| ING-24 | No header row | Fail or treat first row as data; prefer explicit mapping UI | P1 | 6 |
| ING-25 | Header row not on line 1 (metadata preamble) | Skip preamble rows; detect header by keyword match | P1 | 1 |
| ING-26 | Ambiguous column names (`Txn`, `Particulars`, `Narration`) | Heuristic match; if confidence low, return schema for manual mapping | P0 | 1, 6 |
| ING-27 | Missing date column entirely | 400 + prompt column mapping UI | P0 | 1 |
| ING-28 | Missing amount column (no debit/credit/amount) | 400 + prompt column mapping | P0 | 1 |
| ING-29 | Both single `amount` column and separate debit/credit columns | Prefer debit/credit if populated; else signed amount | P0 | 1 |
| ING-30 | Extra unused columns (balance, cheque no., ref) | Ignore gracefully; do not fail | P0 | 1 |
| ING-31 | Column order varies between bank exports | Heuristic mapping by name, not position | P0 | 1 |

### 1.3 Session & upload flow

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| ING-40 | Upload before session created | 404 or auto-create session per product decision | P1 | 1 |
| ING-41 | Upload to non-existent session ID | 404 *"Session not found"* | P0 | 1 |
| ING-42 | Second upload to same session (overwrite) | Replace prior file and invalidate cached analysis; re-analyze required | P1 | 1 |
| ING-43 | Analyze called before upload | 400 *"No statement uploaded"* | P0 | 1 |
| ING-44 | Double-click analyze / duplicate analyze requests | Idempotent or reject in-flight duplicate; no corrupt state | P1 | 1 |
| ING-45 | Access session after TTL expiry (24h) | 404 *"Session expired"*; prompt re-upload | P0 | 5 |
| ING-46 | DELETE session while analysis running | Cancel or wait; purge all temp files and DB rows | P1 | 1, 5 |

---

## 2. Extraction & Cleaning

### 2.1 Dates

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| EXT-01 | Mixed date formats in same file (`DD-MM-YYYY` and `DD/MM/YY`) | Parse each row independently; normalize to ISO | P0 | 1 |
| EXT-02 | Two-digit year (`01-03-24`) | Resolve to 2024; define pivot rule (e.g., 70–99 → 1900s) | P1 | 1 |
| EXT-03 | Invalid date (`31-02-2025`, `00-01-2025`) | Skip row; increment `skippedRows` count | P0 | 1 |
| EXT-04 | Date as Excel serial number | Convert serial to ISO date | P2 | 6 |
| EXT-05 | Timestamp with time (`2025-01-15 14:32:00`) | Strip time; store date only | P0 | 1 |
| EXT-06 | Future-dated transaction | Accept; include in metrics (may be scheduled/post-dated) | P1 | 1 |
| EXT-07 | Transactions spanning year boundary (Dec–Jan statement) | Correct monthly aggregation across years | P0 | 3 |
| EXT-08 | Statement covers single day only | Valid; period start = period end | P1 | 3 |

### 2.2 Amounts

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| EXT-10 | Amount with currency symbol (`₹1,234.56`, `Rs. 500`) | Strip symbols and commas; parse float | P0 | 1 |
| EXT-11 | Indian numbering (`1,23,456.78`) | Parse correctly | P0 | 1 |
| EXT-12 | Parentheses for negative (`(500.00)`) | Treat as debit / negative amount | P1 | 1 |
| EXT-13 | Both debit and credit populated on same row | Prefer non-empty; if both, net or flag as invalid | P0 | 1 |
| EXT-14 | Zero amount (`0.00`) | Skip or include with zero; exclude from spend/income totals | P1 | 1, 3 |
| EXT-15 | Debit and credit columns both empty | Skip row | P0 | 1 |
| EXT-16 | Amount in paise without decimal (integer only) | Parse as rupees unless format indicates paise | P1 | 1 |
| EXT-17 | Scientific notation (`1.5e3`) | Parse as 1500 | P2 | 1 |
| EXT-18 | Refund shown as credit with same description as original purchase | Keep both; dedup only if exact hash match | P1 | 1 |
| EXT-19 | Reversal / chargeback entries | Include in totals; optional tag in metadata | P2 | 3 |

### 2.3 Descriptions & merchants

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| EXT-20 | Empty or whitespace-only description | Skip row or categorize as `Other` with low confidence | P0 | 1, 2 |
| EXT-21 | Extremely long description (500+ chars) | Truncate for display; keep full in `rawDescription` | P1 | 1 |
| EXT-22 | UPI string: `UPI/123456789/SWIGGY/ paytmqr` | Extract merchant `Swiggy`; normalize case | P0 | 1, 2 |
| EXT-23 | IMPS/NEFT/RTGS reference-only text | Clean noise; merchant may remain unknown | P0 | 1 |
| EXT-24 | Masked card: `POS 1234XXXX5678 AMAZON` | Extract `AMAZON`; strip card digits | P0 | 1, 2 |
| EXT-25 | Same merchant, different UPI handles | Group by extracted merchant token for recurring | P1 | 3 |
| EXT-26 | Generic description: `UPI Transfer`, `NEFT Cr` | Low-confidence categorization; LLM or `Other` | P0 | 2 |
| EXT-27 | Salary credited with non-standard narration | Rule match on `SALARY`, `PAYROLL`; else LLM | P0 | 2 |
| EXT-28 | Special characters and emoji in description | Preserve alphanumeric; do not crash parser | P1 | 1 |
| EXT-29 | HTML entities or encoded strings | Decode or strip | P2 | 1 |

### 2.4 Deduplication

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| EXT-30 | Exact duplicate rows (same date, amount, description) | Keep one; report deduped count | P0 | 1 |
| EXT-31 | Same transaction, slightly different description (bank re-post) | May not dedupe; acceptable for MVP | P2 | 1 |
| EXT-32 | Legitimate two purchases same day, same amount, same merchant | Do not incorrectly dedupe; hash includes full normalized description | P0 | 1 |
| EXT-33 | Internal transfer between own accounts (same amount, both debit/credit) | Include both unless transfer detection added (Phase 6) | P2 | 6 |

---

## 3. Categorization

### 3.1 Rule engine

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| CAT-01 | Description matches multiple category keywords (e.g., `AMAZON FOOD`) | Longest match or priority order; document precedence rules | P0 | 2 |
| CAT-02 | Keyword match on substring false positive (`UBER EATS` vs generic `EATS`) | Prefer whole-token or ordered rules | P1 | 2 |
| CAT-03 | Unknown merchant, no rule match | Send to LLM batch; fallback `Other` at 0.3 confidence | P0 | 2 |
| CAT-04 | Credit transaction (refund) for Shopping purchase | Categorize as `Shopping` or `Other`; do not count as income unless Salary-like | P1 | 2, 3 |
| CAT-05 | Investment redemption (credit from Zerodha) | `Investments`, not `Salary` | P0 | 2 |
| CAT-06 | Cash withdrawal ATM | `Other` or dedicated handling; not Food/Shopping | P1 | 2 |
| CAT-07 | Government tax payment (TDS, GST) | `Bills` or `Other` | P1 | 2 |
| CAT-08 | Peer P2P UPI (person name only) | `Other`; low confidence | P1 | 2 |
| CAT-09 | EMI vs large one-time loan prepayment | EMI keywords + recurring signal for EMI category | P1 | 2, 3 |

### 3.2 LLM categorization

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| CAT-20 | LLM API timeout | Fall back to rules-only; mark unmatched as `Other`, confidence 0.3 | P0 | 2 |
| CAT-21 | LLM returns invalid category name | Map to `Other`; log internally without PII | P0 | 2 |
| CAT-22 | LLM returns malformed JSON | Retry batch once; then fallback | P0 | 2 |
| CAT-23 | LLM rate limit / 429 | Exponential backoff; partial results + rules fallback | P1 | 2 |
| CAT-24 | No API key configured | Rules-only mode; pipeline still completes | P0 | 2 |
| CAT-25 | Identical descriptions in batch (100× Swiggy) | Cache by description hash; single LLM call | P1 | 2 |
| CAT-26 | Very small amount (₹1–₹5) — likely micro-subscription test | Still categorize; may cluster as Subscriptions if recurring | P2 | 2, 3 |
| CAT-27 | LLM hallucinates wrong category for ambiguous tx | User override + confidence UI (Phase 6) | P1 | 4, 6 |

### 3.3 User overrides

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| CAT-30 | Override transaction category via PATCH | Update tx; set `categorySource: user`, confidence 1.0 | P0 | 2, 4 |
| CAT-31 | Override triggers re-aggregation | Recalculate categories, metrics, insights for session | P0 | 2, 3 |
| CAT-32 | Override same merchant on multiple transactions | Session rule applies to all matching merchants | P0 | 2 |
| CAT-33 | Override to invalid category enum | 400 validation error | P0 | 2 |
| CAT-34 | PATCH on non-existent transaction ID | 404 | P0 | 2 |
| CAT-35 | Override after session expired | 404 | P1 | 5 |

---

## 4. Recurring Detection

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| REC-01 | Statement period < 2 months | Insufficient history; empty recurring list + explanation | P0 | 3 |
| REC-02 | Only one occurrence of Netflix | Do not mark recurring (needs ≥2 occurrences) | P0 | 3 |
| REC-03 | Same amount but irregular dates (not monthly) | Do not classify as monthly recurring; optional `other` if 2+ occurrences | P1 | 3 |
| REC-04 | Subscription price changed mid-period (₹199 → ₹249) | ±5% tolerance may fail; may split into two groups | P1 | 3 |
| REC-05 | Annual insurance premium (once in statement) | Single occurrence → not recurring in window | P1 | 3 |
| REC-06 | Quarterly SIP (3 occurrences in 9 months) | Detect `quarterly` if interval matches | P2 | 3 |
| REC-07 | Weekly food delivery same merchant | May false-positive as subscription; use amount + category heuristics | P1 | 3 |
| REC-08 | EMI and rent same amount different merchants | Separate recurring groups by fingerprint | P0 | 3 |
| REC-09 | Salary credited monthly | Detect as recurring credit; exclude from recurring *debit* total or show separately | P1 | 3 |
| REC-10 | Duplicate EMI debit (bank error, same day) | Dedup at extraction; recurring count unaffected | P1 | 1, 3 |
| REC-11 | Free trial then paid subscription (₹0 then ₹499) | Amount variance fails; may miss until paid cycles exist | P2 | 3 |
| REC-12 | UPI autopay with varying amounts (electricity bill) | High variance; likely not flagged as fixed recurring | P1 | 3 |

---

## 5. Metrics & Aggregations

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| MET-01 | No credit transactions (spend-only statement) | `totalIncome = 0`; savings negative; show clearly | P0 | 3 |
| MET-02 | No debit transactions (salary-only) | `totalSpend = 0`; insights adapted | P0 | 3 |
| MET-03 | Zero transactions after cleaning | Empty state; no divide-by-zero on percentages | P0 | 3, 4 |
| MET-04 | Savings rate when income is zero | Omit savings rate or show *"N/A"*; never `NaN`/`Infinity` | P0 | 3 |
| MET-05 | All spend in one category | Top category = 100%; chart renders single slice | P0 | 3, 4 |
| MET-06 | Period filter excludes all transactions | Empty summary for range; UI message | P1 | 3, 6 |
| MET-07 | `from` date after `to` date in query param | 400 validation error | P1 | 3 |
| MET-08 | Biggest transaction tie (same amount) | Return first by date or list all in metadata | P1 | 3 |
| MET-09 | Internal transfer counted in spend and income | Inflated totals; document as known limitation until Phase 6 | P2 | 6 |
| MET-10 | Refunds reduce net spend or shown separately | Define policy: net spend = debits − credit refunds in non-Salary categories | P1 | 3 |
| MET-11 | Investment SIP counted in spend and Investments | Accept double semantic; or SIP as Investments only | P1 | 3 |
| MET-12 | Floating-point rounding (₹0.01 drift) | Round display to 2 decimals; consistent sums | P0 | 3 |

---

## 6. Insights Generation

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| INS-01 | Fewer than 3 obvious insights (minimal data) | Always return ≥3: use fallbacks (tx count, date range, avg spend) | P0 | 3 |
| INS-02 | Single-month statement (no month comparison) | Skip month-comparison template; use other templates | P0 | 3 |
| INS-03 | No recurring payments detected | Skip recurring-burden template; substitute another | P0 | 3 |
| INS-04 | Negative savings (spent more than earned) | Insight: *"You spent ₹X more than you earned"* | P0 | 3 |
| INS-05 | LLM polish fails | Return deterministic template strings | P0 | 3 |
| INS-06 | Top category is `Other` (low rule coverage) | Still valid insight; suggest reviewing uncategorized tx | P1 | 3, 4 |
| INS-07 | All amounts zero / empty metrics | Generic guidance insights; no fabricated amounts | P0 | 3 |
| INS-08 | Insight amounts must match dashboard totals | Single source of truth from metrics engine | P0 | 3 |

---

## 7. API & Pipeline

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| API-01 | GET summary before analyze completes | 409 or 202 with *"Processing"*; frontend polls status | P0 | 1, 4 |
| API-02 | Invalid session UUID format | 400 Bad Request | P1 | 0 |
| API-03 | Pipeline stage throws unhandled exception | Status → `error`; user message without stack trace or file contents | P0 | 1 |
| API-04 | Partial pipeline failure (extract OK, categorize fails) | Isolate failure; return partial data if safe, else error with stage name | P1 | 1 |
| API-05 | Pagination: `page` beyond range | Empty list, not 404 | P1 | 1 |
| API-06 | Pagination: negative page or limit > max | 400 or clamp to defaults | P1 | 1 |
| API-07 | Concurrent requests to same session | SQLite locking; last-write-wins or queue | P2 | 0 |
| API-08 | CORS blocked from frontend origin | Configure allowed origins in dev/prod | P0 | 0 |
| API-09 | API down during frontend poll | Retry with backoff; show connection error | P1 | 4 |

---

## 8. Frontend & UX

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| UI-01 | User closes tab during analysis | Session persists; user can return via URL if session ID saved | P1 | 4 |
| UI-02 | Browser refresh on dashboard | Reload data from API by session ID in route | P0 | 4 |
| UI-03 | Invalid session ID in URL | Show error + link to upload | P0 | 4 |
| UI-04 | Drag-and-drop non-file object | Ignore; no crash | P1 | 4 |
| UI-05 | Upload multiple files at once | Accept first only or reject with single-file message | P1 | 4 |
| UI-06 | Very long transaction list (1,000+ rows) | Paginate or virtualize table; API pagination | P1 | 4 |
| UI-07 | Pie chart with 10 categories + tiny slices | Label threshold or legend list | P1 | 4 |
| UI-08 | All categories zero spend | Empty chart + message | P0 | 4 |
| UI-09 | Category override network failure | Toast error; revert dropdown selection | P1 | 4 |
| UI-10 | Narrow mobile viewport | Layout not broken; tables scroll horizontally | P1 | 4 |
| UI-11 | Rupee formatting (`₹12,34,567.89`) | Consistent locale formatting across views | P1 | 4 |
| UI-12 | User navigates away without deleting session | Privacy notice reminds; TTL cleans up server-side | P1 | 4, 5 |

---

## 9. Report Export

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| RPT-01 | Generate report before analysis complete | 409 or blocking wait | P0 | 5 |
| RPT-02 | PDF engine (WeasyPrint) missing in Docker | Fallback to HTML download + browser print | P1 | 5 |
| RPT-03 | Report with 0 transactions | Minimal report with empty-state text | P1 | 5 |
| RPT-04 | Very long report (500+ tx in appendix) | Truncate appendix or paginate PDF | P2 | 5 |
| RPT-05 | Special characters in merchant names break HTML | Escape entities in template | P0 | 5 |
| RPT-06 | Charts in PDF | Use tables/static summaries per architecture | P0 | 5 |
| RPT-07 | Session deleted during report download | Abort with 404 | P1 | 5 |

---

## 10. Security & Privacy

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| SEC-01 | Malicious filename (`../../etc/passwd.csv`) | Sanitize; store under session UUID path only | P0 | 1, 5 |
| SEC-02 | Statement content logged on error | Never log raw descriptions or amounts | P0 | All |
| SEC-03 | Session ID guessable (sequential integers) | Use UUID v4 for session IDs | P0 | 0 |
| SEC-04 | Sensitive data in URL query params | Never pass transaction data in URLs | P0 | 4, 5 |
| SEC-05 | Uploaded file served back as static asset | Files not publicly accessible; API auth by session | P0 | 1 |
| SEC-06 | XSS via transaction description in UI | Escape on render | P0 | 4 |
| SEC-07 | API keys in client bundle | LLM calls server-side only | P0 | 2 |
| SEC-08 | Temp files not deleted on crash | TTL cleanup job removes orphaned files | P1 | 5 |
| SEC-09 | User uploads another person's statement | Privacy notice; no account binding; user responsibility | P1 | 4 |

---

## 11. Deployment & Environment

| ID | Edge case | Expected behavior | Priority | Phase |
|----|-----------|-------------------|----------|-------|
| DEP-01 | SQLite file on read-only filesystem | Document volume mount in Docker | P0 | 0, 5 |
| DEP-02 | `/tmp` full during upload | Graceful 507 error | P2 | 5 |
| DEP-03 | Missing `LLM_API_KEY` in production | Rules-only mode; no startup crash | P0 | 2, 5 |
| DEP-04 | Frontend `API_URL` misconfigured | Health check fails visibly in dev | P0 | 0 |
| DEP-05 | Clock skew across containers | Use UTC consistently for TTL | P1 | 5 |
| DEP-06 | Ollama not running (local mode) | Clear error: *"Local LLM unavailable"* | P2 | 6 |

---

## 12. Real-World Indian Banking Scenarios

High-value test scenarios reflecting messy descriptions from the problem statement:

| ID | Scenario | Sample pattern | Expected handling |
|----|----------|----------------|-------------------|
| IND-01 | UPI food delivery | `UPI-SWIGGY@ybl/123/PM` | Food, merchant Swiggy |
| IND-02 | Multi-app same category | Zomato + Swiggy + Dominos | All Food; top category insight |
| IND-03 | Monthly rent via NEFT | `NEFT DR LANDLORD NAME` | Rent; recurring if ≥2 months |
| IND-04 | Netflix subscription | Fixed ₹649 monthly | Subscriptions, recurring |
| IND-05 | Home loan EMI | `NACH HDFC HOME LOAN` | EMI, recurring |
| IND-06 | Mutual fund SIP | `BSE SIP GROWW` | Investments, recurring |
| IND-07 | Salary credit | `SALARY JAN 2025 ACME CORP` | Salary, income metric |
| IND-08 | Electricity bill (variable) | `BESCOM UPI` varying amounts | Bills; likely not fixed recurring |
| IND-09 | Amazon mixed cart | `AMAZON PAY` only in description | Shopping (ambiguous vs Bills) |
| IND-10 | IRCTC + Uber same week | Multiple Travel vendors | Travel sub-aggregate in insights |
| IND-11 | Credit card bill payment | `CC PAYMENT HDFC` | Exclude from spend or tag `Other` |
| IND-12 | Cashback credit | Small credit from merchant | Reduce spend or ignore in income |
| IND-13 | Failed UPI reversed | Debit then credit same day | Net effect or show both |
| IND-14 | Joint account multiple spenders | Mixed merchants | Still aggregate; no per-user split |
| IND-15 | FD interest credit | `INT PD FD` | Investments or Other income |

---

## 13. Stage Failure Matrix (Quick Reference)

From architecture §6 — consolidated for implementers:

| Stage | Trigger | System response | User sees |
|-------|---------|-----------------|-----------|
| Ingestion | Bad format / missing columns | Stop or request mapping | Supported formats + mapping UI |
| Extract | Bad rows | Continue with valid rows | *"X rows skipped"* |
| Categorize | LLM down | Rules + `Other` fallback | Dashboard works; low-confidence badge |
| Recurring | Short history | Empty list | *"Not enough data to detect recurring payments"* |
| Metrics | No transactions | Zeroed summary | Empty state + upload guidance |
| Insights | Any failure | Template insights only | ≥3 insight cards always |

---

## 14. MVP vs Deferred Summary

### Must test before submission (P0 checklist)

- [ ] Empty file, wrong format, oversized file
- [ ] Missing date/amount columns
- [ ] Mixed dates and Indian amount formats
- [ ] Duplicate row deduplication
- [ ] UPI merchant extraction (Swiggy, Amazon, etc.)
- [ ] LLM unavailable → rules-only path
- [ ] Zero transactions empty state
- [ ] No income / no spend metrics
- [ ] Always ≥3 insights
- [ ] Recurring with <2 months data
- [ ] Session expiry and delete
- [ ] No PII in logs; sanitized filenames
- [ ] Dashboard refresh and invalid session URL

### Document as known limitations (acceptable for MVP)

- Multi-bank PDF without template
- Internal transfer double-counting
- Variable utility bills as recurring
- Password-protected files
- Single-day duplicate merchant purchases not deduped
- Credit card bill payment categorization

---

## 15. Sample Test Data Requirements

Build fixtures covering:

1. **happy_path.csv** — 100+ rows, 3 months, mixed categories, known recurring
2. **messy_dates.csv** — Mixed `DD-MM-YYYY` / `DD/MM/YY`
3. **missing_columns.csv** — For mapping UI testing
4. **duplicates.csv** — Exact duplicate rows
5. **sparse.csv** — Headers only / 3 rows
6. **salary_only.csv** — Credits only
7. **spend_only.csv** — Debits only
8. **upi_heavy.csv** — Realistic UPI narrations

---

## References

- [architecture.md](./architecture.md) — Stage contracts, failure modes, data models
- [implementation-plan.md](./implementation-plan.md) — Phase tasks and acceptance criteria
- [context.md](./context.md) — Product requirements and evaluation criteria
