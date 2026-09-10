# Worked Examples — real boards created with this system

Two real projects/boards were built end-to-end using these skills (project → workflow → scheme →
board with `location` → auto column split via greenhopper). They serve as reference templates for
adapting to new domains.

## 1. Server Management Dashboard (`SRV`, board 233)
A web app for managing server inventory (name, location, IP) stored in MongoDB.

**Statuses → status IDs:**
```
Backlog(10098) → PM Definition(10099) → Architecture Design(10100) → Development(10010)
→ QA Testing(10101) → Security Review(10064) → Done(10005)
```
**Script:** `scripts/setup_server_board.py` (created locally; same pattern as `setup_kafka_board.py`).

## 2. Kafka Investigation (`KFK`, board 234)
Investigating a Kafka issue (triage → root cause → resolution → verify).

**Statuses → status IDs:**
```
New(10102) → Triage(10103) → Investigation(10104) → Root Cause Identified(10105)
→ Resolution(10106) → Verification(10107) → Closed(6)
```
**Script:** `scripts/setup_kafka_board.py` — a ready-to-run template for an investigation/ops board.

---

## How to reuse for a new domain
1. Copy `scripts/setup_kafka_board.py` (or `setup_team_board.py`) to a new file.
2. Edit the `NAME`, `KEY`, and the `roles = [...]` list at the top to your domain's statuses
   (format: `("StatusName", "TODO|IN_PROGRESS|DONE")`).
3. Run it → creates project + workflow + scheme + filter + board (with `location`).
4. Run `scripts/set_columns.py <boardId> "StatusName:StatusId" ...` to split into one column per status.
   (Get status ids via `GET /rest/api/3/statuses/search`.)
5. Verify via re-GET (editmodel.json) + create a test issue.
