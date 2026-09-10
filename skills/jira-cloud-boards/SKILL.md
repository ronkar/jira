---
name: jira-cloud-boards
description: "Use when creating Jira Cloud boards/workflows via API."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [jira, atlassian, kanban, workflow, board, api]
    category: productivity
---

# Jira Cloud Boards, Statuses & Workflows (via API)

Create real Kanban boards with custom role columns on Atlassian **Jira Cloud** using the REST API. This skill captures the exact endpoints and payload formats that took significant trial-and-error to discover.

## When to Use
- Creating a Kanban/Scrum board with custom columns (e.g. one column per agent role).
- Creating custom statuses for a project.
- Creating a workflow with custom statuses + transitions via API.

## Prerequisites / Credentials
- Credentials file: `/root/jira_cloud/credentials.env` (JIRA_BASE, JIRA_EMAIL, JIRA_TOKEN).
- Helper script: `/root/jira_cloud/jira.sh` — usage:
  ```
  ./jira.sh GET  /rest/api/3/project/search
  ./jira.sh POST /rest/api/3/issue '{"fields":{...}}'
  ./jira.sh search 'project = AG'     # JQL search (uses /search/jql)
  ```
- Auth is **Basic auth: email + API token** (token from https://id.atlassian.com/manage-profile/security/api-tokens).

## Key Endpoints (the hard-won part)
| Task | Endpoint | Notes |
|------|----------|-------|
| List projects | `GET /rest/api/3/project/search` | |
| Create board | `POST /rest/agile/1.0/board` | body `{"name","type":"kanban","filterId":<id>}` |
| Create filter | `POST /rest/api/3/filter` | body `{"name","jql","favourite":true}` |
| Create statuses | `POST /rest/api/3/statuses` | statusCategory = **TODO/IN_PROGRESS/DONE** (uppercase) |
| **Create workflow** | **`POST /rest/api/3/workflows/create`** | see payload below |
| List workflows | `GET /rest/api/3/workflow/search` | |
| JQL search | `POST /rest/api/3/search/jql` | body `{"jql":"...","maxResults":50}` |

## CRITICAL pitfalls (learned the hard way)
1. **Workflow creation endpoint is `POST /rest/api/3/workflows/create`** (plural + `/create`).
   - `POST /rest/api/3/workflow` (singular) → **405 Method Not Allowed** (wrong).
   - `POST /rest/api/3/workflows` (plural, no /create) → this is the **READ** endpoint (WorkflowReadRequest), returns "Invalid request payload" for create bodies.
2. **Transition `id` must be a numeric string** ("1","2",...) — UUIDs fail with "Invalid format".
3. **statusCategory must be uppercase** `TODO` / `IN_PROGRESS` / `DONE` (not "To Do", not 2/4/3, not lowercase).
4. **Scope type**: `GLOBAL` for company-managed (classic) projects, `PROJECT` for team-managed (next-gen) projects.
   - Company-managed: `statusReference` = the status ID (numeric string).
   - Team-managed: `statusReference` must be a **UUID**.
5. Board columns are derived from the **workflow statuses** — you cannot set board columns directly (PUT/POST on `/rest/agile/1.0/board/{id}/configuration` → 405). To get custom columns, the project's workflow must contain those statuses.
6. Status names must be unique globally (e.g. "Security" already exists → use "Security Review").
7. **CRITICAL — board MUST be created with `location`**: `{"name":"X","type":"kanban","filterId":<id>,"location":{"projectKeyOrId":"<KEY>","type":"project"}}`. Without `location`, the board has NO project association and the Jira frontend fails to render it with **"Something went wrong on our end"** (hash N9JYK3 / DLPJAU). A working board (e.g. the default "AG board") always has `location`; API-created boards without it crash the UI even though the API returns issues fine. Also note the created board's `ranking` stays `{}` — that's expected; the `location` is what matters for rendering.
8. **Board can't be updated in place**: `PUT /rest/agile/1.0/board/{id}` → 405 (only GET/DELETE). To fix a broken board you must DELETE it and recreate WITH `location`. `PUT /rest/agile/1.0/board/{id}/configuration` → 405 too (columns not settable via API).
9. **Workflow scheme can only be assigned to an EMPTY project** — "Only empty projects can have workflow schemes assigned." Assign the scheme BEFORE creating any issues, or you'll be locked out of changing it.
10. **Project styles**: `style: next-gen` = team-managed (scope PROJECT, statusReference=UUID); `style: classic` = company-managed (scope GLOBAL, statusReference=status id). Check with `GET /rest/api/3/project/{key}`.

## Creating a workflow (working payload)
Generate statusReferences (UUIDs) and transition ids (numeric strings) in Python, then POST to `/rest/api/3/workflows/create`:

```python
import json, uuid
roles = [("Manager","TODO"),("Architect","IN_PROGRESS"),("Developer","IN_PROGRESS"),
         ("Tester","IN_PROGRESS"),("Security Review","IN_PROGRESS"),("PM","DONE")]
refs = {name: str(uuid.uuid4()) for name,_ in roles}
statuses = [{"name":n,"statusCategory":c,"statusReference":refs[n]} for n,c in roles]
wf_statuses = [{"statusReference":refs[n],"properties":{}} for n,_ in roles]
transitions = [{"id":"1","name":"Start","type":"INITIAL","toStatusReference":refs["Manager"],"links":[]}]
for i,(s,d) in enumerate([("Manager","Architect"),("Architect","Developer"),("Developer","Tester"),
                          ("Tester","Security Review"),("Security Review","PM")], start=2):
    transitions.append({"id":str(i),"name":f"To {d}","type":"DIRECTED",
                        "toStatusReference":refs[d],"links":[{"fromStatusReference":refs[s]}]})
payload = {"scope":{"type":"GLOBAL"},"statuses":statuses,
           "workflows":[{"name":"My Workflow","description":"...","statuses":wf_statuses,"transitions":transitions}]}
# POST payload to /rest/api/3/workflows/create
```

Then **assign the workflow to a project** via a workflow scheme (or in the Jira UI: Admin → Workflow schemes → assign to project). After assignment, create/recreate the board so its columns reflect the workflow statuses.

## Full end-to-end flow (working recipe)
Order matters — assign the scheme to an EMPTY project, then create issues. Steps:

1. **Create project** (company-managed/classic so scope=GLOBAL is simple):
   `POST /rest/api/3/project` body `{"key":"<KEY>","name":"<Name>","projectTypeKey":"software","leadAccountId":"<accountId>"}` → note project id.
2. **Create workflow** with role statuses + transitions → `POST /rest/api/3/workflows/create` (see payload above). Use a UNIQUE name (names collide globally). Reuse existing GLOBAL statuses by passing `{"id":"<sid>","name":"...","statusCategory":"...","statusReference":"<sid>"}`.
3. **Create workflow scheme**: `POST /rest/api/3/workflowscheme` body `{"name":"<Scheme>","defaultWorkflow":"<WorkflowName>"}` → note scheme id.
4. **Assign scheme to project** (project MUST be empty): `PUT /rest/api/3/workflowscheme/project` body `{"projectId":"<id>","workflowSchemeId":"<schemeId>"}`.
5. **Create filter**: `POST /rest/api/3/filter` body `{"name":"<Name> - All","jql":"project = <KEY> ORDER BY created DESC","favourite":true}` → note filter id.
6. **Create board WITH location** (the critical step): `POST /rest/agile/1.0/board` body `{"name":"<Name>","type":"kanban","filterId":<filterId>,"location":{"projectKeyOrId":"<KEY>","type":"project"}}` → note board id.
7. **Verify via API**: `GET /rest/agile/1.0/board/{id}` → confirm `location` is present (this is what makes the UI render). `GET /rest/agile/1.0/board/{id}/issue` → returns issues. Create a test issue → confirm it lands in the initial status and transitions work.
8. **Verify UI**: open `https://<site>.atlassian.net/jira/software/projects/<KEY>/boards/<boardId>` — must load WITHOUT "Something went wrong on our end". If it errors, the board is missing `location` → delete + recreate with location.

## Setting board columns (undocumented greenhopper API) — WORKS
The official `PUT /rest/agile/1.0/board/{id}/configuration` → 405 (read-only). BUT there is an undocumented family of endpoints under `/rest/greenhopper/1.0/rapidviewconfig/...` that WORKS with normal Basic auth (email + API token) — no browser, no session.

**Read the current column config (what the UI loads for Configure → Columns):**
```
GET /rest/greenhopper/1.0/rapidviewconfig/editmodel.json?rapidViewId={boardId}
```
Returns `rapidListConfig.mappedColumns[]` — each column has `id`, `name`, `mappedStatuses[]` (status objects with `id`,`name`).

**Set the columns (split into one column per status):**
```
PUT /rest/greenhopper/1.0/rapidviewconfig/columns
Content-Type: application/json
Authorization: Basic {base64(email:api_token)}
{
  "rapidViewId": {boardId},
  "mappedColumns": [
    {"name": "Backlog", "mappedStatuses": [{"id": "10098"}]},
    {"name": "PM Definition", "mappedStatuses": [{"id": "10099"}]},
    ... one per status ...
  ]
}
```
- `mappedStatuses[].id` = the **status id** (from `GET /rest/api/3/statuses/search`). Get each status's numeric id first.
- Returns 200 + the updated `rapidListConfig` in the body.
- **VERIFY by re-GETting** `editmodel.json` (or the official `GET /rest/agile/1.0/board/{id}/configuration`) and confirm each status now has its own column. Do NOT trust the 200 alone.
- Note: kanban boards show an extra empty "Backlog" plan column (`isKanPlanColumn:true`) on top of the status columns — that's a normal kanban feature, not an error.

## Verify
- `GET /rest/api/3/workflow/search` → confirm the workflow name + entityId exist.
- `GET /rest/agile/1.0/board` → confirm the board exists.
- Open the board URL in the browser: `https://<site>.atlassian.net/jira/software/projects/<KEY>/boards/<boardId>`.

## Notes
- Jira Cloud API **cannot** change: sidebar color, card layout/design, or custom theme colors. Board columns must come from workflow statuses.
- The reference design (light theme, blue/teal accents) is matched via status category colors + labels + avatars only.
