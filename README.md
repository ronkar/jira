# Jira Cloud Automation — Skills & Learnings

Everything learned about automating **Jira Cloud** (`ronkarny5547.atlassian.net`) via the REST API.
This repo is designed so a **new agent can adopt these as its own skills** and immediately
create dynamic projects / boards / workflows / columns without re-discovering the hard-won details.

> **Credentials:** the scripts read `JIRA_BASE`, `JIRA_EMAIL`, `JIRA_TOKEN` from
> `/root/jira_cloud/credentials.env` (Basic auth: email + API token). No secrets are stored in this repo.

---

## 📚 Skills (drop into your agent's `skills/` dir)

| Skill | Purpose |
|-------|---------|
| `skills/jira-cloud-boards/` | Create boards/workflows/statuses via API + **split columns** via the undocumented greenhopper API. |
| `skills/jira-dynamic-workflow/` | The **agent role**: analyze a business need → propose workflow → get approval → execute → report. |
| `skills/jira-cloud-api/` | General Jira Cloud REST automation (projects, statuses, workflows, issues). |

---

## 🚀 Quick start for a new agent

1. **User describes a business need** (e.g. "a server-management web app").
2. Follow `skills/jira-dynamic-workflow/SKILL.md` — analyze → propose → **get approval** → execute.
3. Execute with the scripts below.

### Full flow (all automatic, incl. columns)
```bash
# 1. Create project + workflow + scheme + filter + board (WITH location)
python3 scripts/setup_team_board.py "<Project Name>" <KEY>

# 2. Split the board into one column per status (undocumented greenhopper API, verified)
python3 scripts/set_columns.py <boardId> "Backlog:10098" "PM Definition:10099" ...
```

---

## 🔑 The two critical hard-won facts

### 1. Board MUST be created with `location`
```json
POST /rest/agile/1.0/board
{"name":"X","type":"kanban","filterId":<id>,"location":{"projectKeyOrId":"<KEY>","type":"project"}}
```
Without `location` the board has **no project association** and the Jira UI crashes with
**"Something went wrong on our end"** — even though the API returns issues fine.
Boards can't be updated in place (`PUT /board/{id}` → 405); you must delete + recreate with `location`.

### 2. Columns CAN be set via the undocumented greenhopper API
The official `PUT /rest/agile/1.0/board/{id}/configuration` → **405** (read-only). But this works:

```bash
# Read current column config
GET /rest/greenhopper/1.0/rapidviewconfig/editmodel.json?rapidViewId={boardId}

# Set columns (one per status)
PUT /rest/greenhopper/1.0/rapidviewconfig/columns
Content-Type: application/json
Authorization: Basic {base64(email:api_token)}
{
  "rapidViewId": 233,
  "mappedColumns": [
    {"name": "Backlog", "mappedStatuses": [{"id": "10098"}]},
    {"name": "Done",    "mappedStatuses": [{"id": "10005"}]}
  ]
}
```
**Always verify by re-GETting** `editmodel.json` after writing — don't trust the 200 alone.

---

## 🧩 Workflow creation (the endpoint that took trial-and-error)

- **Correct endpoint:** `POST /rest/api/3/workflows/create` (plural + `/create`)
- `POST /rest/api/3/workflow` (singular) → **405**
- `POST /rest/api/3/workflows` (no `/create`) → this is the **READ** endpoint
- Transition `id` must be a **numeric string** ("1","2",...)
- `statusCategory` must be **uppercase**: `TODO` / `IN_PROGRESS` / `DONE`
- Scope: `GLOBAL` for company-managed (statusReference = status id); `PROJECT` for team-managed (statusReference = UUID)
- Status names must be globally unique (e.g. "Security" taken → "Security Review")
- Workflow scheme can only be assigned to an **EMPTY** project

---

## 🗂️ Repo layout
```
README.md              ← you are here
skills/
  jira-cloud-boards/    SKILL.md + scripts (create_workflow.py, setup_team_board.py, set_columns.py)
  jira-dynamic-workflow/ SKILL.md (the agent role)
  jira-cloud-api/       SKILL.md (general REST automation)
scripts/               copies of the ready-to-run Python scripts
docs/                  detailed endpoint reference
```

See `docs/endpoints.md` for the full endpoint/payload reference.
