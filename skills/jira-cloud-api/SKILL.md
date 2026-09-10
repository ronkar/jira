---
name: jira-cloud-api
description: "Automate Jira Cloud via REST: projects, statuses, workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [jira, atlassian, rest, workflow, statuses, projects, api]
---

# Jira Cloud REST API

Drive Jira Cloud programmatically: connect with an API token, create
company-managed projects, custom statuses, and full workflows. Use whenever the
user wants to create/manage Jira projects, statuses, workflows, or issues via API.

## Auth

Basic auth with `email:API_token`:
```bash
curl -u "$EMAIL:$TOKEN" "$BASE/rest/api/2/myself"        # verify identity
curl -u "$EMAIL:$TOKEN" "$BASE/rest/api/2/project"        # list projects
```
- `$BASE` = `https://<your-org>.atlassian.net`
- API token created at `https://id.atlassian.com/manage-profile/security/api-tokens`
- `leadAccountId` (needed to create projects) comes from `/rest/api/2/myself` → `accountId`.

## Search issues (JQL)

The old **`GET /rest/api/3/search` endpoint has been REMOVED** — it now returns
`{"errorMessages":["The requested API has been removed. Please migrate to the
/rest/api/3/search/jql API."]}`. Use the replacement **`POST /rest/api/3/search/jql`**:

```bash
curl -u "$EMAIL:$TOKEN" -X POST -H "Content-Type: application/json" \
  -d '{"jql":"project = AG ORDER BY created DESC","maxResults":50}' \
  "$BASE/rest/api/3/search/jql"
```

- The new response shape is `{"issues":[...],"isLast":true}` — there is **no `total`**
  field. Count via `len(issues)`, not `.total`.
- Issue fields: `issue['key']`, `issue['fields']['summary']`,
  `issue['fields']['status']['name']`, `issue['fields']['issuetype']['name']`.
- List a project's issue types: `GET /rest/api/3/project/<KEY>` → `.issueTypes[]`.
- List a project's statuses per issue type:
  `GET /rest/api/3/project/<KEY>/statuses` → `[{name, statuses:[{name}]}]`.

## Project type matters

- **next-gen / team-managed** (`style: "next-gen"`) — **cannot** hold a custom
  workflow via API; only a fixed status set (To Do / In Progress / In Review / Done).
  If the user wants a real multi-stage workflow, create a **company-managed** project.
- **company-managed / classic** — supports custom workflows & statuses via API.
  Check style: `curl .../rest/api/2/project/<KEY>` → `.style` and `.projectTypeKey`.

## Create a company-managed project

```bash
curl -u "$EMAIL:$TOKEN" -X POST -H "Content-Type: application/json" \
  -d '{"key":"REL","name":"Release","projectTypeKey":"software","leadAccountId":"<accountId>"}' \
  "$BASE/rest/api/2/project"
```
- Do **NOT** include a `style` field — it makes the payload invalid
  ("Invalid request payload"). The project comes out company-managed by default.
- Response: `{"id":10033,"key":"REL",...}` — keep the numeric `id`.

## Create custom statuses

Endpoint: **`POST /rest/api/3/statuses`** (the classic `POST /rest/api/2/status`
returns **405** on Jira Free — use api/3 and the plural path).

```json
{
  "scope": {"type": "GLOBAL"},
  "statuses": [
    {"name": "Idea", "statusCategory": "TODO"},
    {"name": "Development", "statusCategory": "IN_PROGRESS"}
  ]
}
```
- **`scope` is TOP-LEVEL**, not inside each status. `GLOBAL` for company-managed
  projects; `PROJECT` (with `project.id`) only for team-managed.
- `statusCategory` enum: `TODO` | `IN_PROGRESS` | `DONE` (NOT `new`/`indeterminate`).
- Response returns each status with its numeric `id` — capture these.
- ⚠️ **The numeric `id` is NOT the `statusReference` the workflow API wants.** The
  workflow creation endpoint validates `statusReference` as a **UUID** and rejects
  numeric ids with `"The reference 10006 is not a UUID."` The status UUIDs are
  **not exposed** by `GET /rest/api/3/statuses` (only numeric id) nor by the
  workflow-scheme/read endpoints — see the workflow section for the consequence.

## Create a workflow

Endpoint: **`POST /rest/api/3/workflows/create`** (the classic
`POST /rest/api/2/workflow` returns **405** on Jira Free).

```json
{
  "scope": {"type": "GLOBAL"},
  "statuses": [
    {"id": "10006", "name": "Idea", "statusCategory": "TODO", "statusReference": "11111111-1111-1111-1111-111111111111"},
    {"id": "10010", "name": "Development", "statusCategory": "IN_PROGRESS", "statusReference": "22222222-2222-2222-2222-222222222222"}
  ],
  "workflows": [{
    "name": "Release Workflow",
    "statuses": [
      {"statusReference": "11111111-1111-1111-1111-111111111111", "properties": {}},
      {"statusReference": "22222222-2222-2222-2222-222222222222", "properties": {}}
    ],
    "transitions": [
      {"id": "1", "name": "Create", "type": "INITIAL", "toStatusReference": "11111111-1111-1111-1111-111111111111"},
      {"id": "2", "name": "To Development", "type": "DIRECTED",
       "toStatusReference": "22222222-2222-2222-2222-222222222222", "links": [{"fromStatusReference": "11111111-1111-1111-1111-111111111111"}]}
    ]
  }]
}
```
- **`statusReference` is a UUID YOU invent yourself** (unique within this one request) —
  it is NOT the status's real UUID, and it is NOT the numeric id. Generate one per
  status with `uuidgen` / `crypto.randomUUID()`.
- **Include the existing status's numeric `id`** in each top-level `statuses` entry.
  This is what tells Jira "reference the already-existing status" instead of trying to
  CREATE a new one. Omitting `id` → `"Status name X already in use"`.
- `statusCategory` must match the category the status was actually created with
  (check `GET /rest/api/3/statuses?id=<id>`); a mismatch triggers another error.
- Each workflow's `statuses` entries need `{statusReference, properties}` (properties
  required) — reference by the SAME invented UUID.
- Each transition: `{id, name, type: DIRECTED, toStatusReference, links:[{fromStatusReference}]}`.
- **Every transition needs an `id`** (string) — otherwise:
  `"Missing required field 'workflows.[0].transitions.[0].id'"`.
- **Exactly one `type: "INITIAL"` transition is required** — it points at the first
  status (`toStatusReference`) with no `links`. Otherwise:
  `"Workflow must have exactly one initial transition."`

### The statusReference trick (solves the "UUID" blocker)

`POST /rest/api/3/workflows/create` validates every `statusReference` as a **UUID**
(even for company-managed, despite the docs claiming otherwise). The status UUIDs are
**not exposed** by `GET /rest/api/3/statuses` (only numeric id) nor by the
workflow-scheme/read endpoints. **That is fine** — `statusReference` is NOT the
status's real UUID. It is a UUID **you invent** per request, unique within that one
request, purely to tie the top-level `statuses` entry to the workflow's `statuses` and
`transitions`. The link to the real status is made by the **numeric `id`** field in the
top-level `statuses` array. So: invent a UUID per status, put the real numeric `id` next
to it, and reuse the invented UUIDs everywhere in the workflow body. This fully works on
Jira Free — no UI fallback needed.

## Assign the workflow to a project (workflow scheme) + publish

The workflow must be attached to the project through its **workflow scheme**, then the
scheme draft published (with status mappings):

```bash
# 1. Find the project's scheme id
curl -u "$EMAIL:$TOKEN" "$BASE/rest/api/3/workflowscheme?projectId=<PROJECT_ID>"
#    -> note the scheme id (e.g. 10034) and its defaultWorkflow

# 2. Create a draft of the scheme (fails with "already has a draft" if one exists — that's fine)
curl -u "$EMAIL:$TOKEN" -X POST -H "Content-Type: application/json" -d '{}' \
  "$BASE/rest/api/3/workflowscheme/10034/createdraft"

# 3. Point the draft's default workflow at the new workflow
curl -u "$EMAIL:$TOKEN" -X PUT -H "Content-Type: application/json" \
  -d '{"workflow":"Release Workflow"}' \
  "$BASE/rest/api/3/workflowscheme/10034/draft/default"

# 4. Publish the draft, supplying statusMappings (old status -> new status) per issue type
curl -u "$EMAIL:$TOKEN" -X POST -H "Content-Type: application/json" \
  -d '{"statusMappings":[{"issueTypeId":"10007","statusId":"10004","newStatusId":"10006"},{"issueTypeId":"10007","statusId":"3","newStatusId":"10010"}]}' \
  "$BASE/rest/api/3/workflowscheme/10034/draft/publish"
```
- `statusMappings` item: `{issueTypeId, statusId (old), newStatusId (new)}`. Get the
  issue-type ids and old status ids from `GET /rest/api/3/project/<KEY>/statuses`.
- **`"Issue type with ID X is missing the mappings required for statuses with IDs Y,Z"`**
  → you must supply a mapping for those (old→new) statuses for that issue type.
- **`"redundant mappings for statuses with IDs X"`** → drop any mapping where the old
  status already equals the new one (e.g. Done→Done is automatic; do NOT include it).
- Publish returns an empty body on success (no error JSON). The project's statuses
  update after a few seconds — verify with `GET /rest/api/3/project/<KEY>/statuses`.
- Verify the workflow end-to-end by creating an issue and walking every transition
  (`GET /rest/api/3/issue/<KEY>/transitions` → POST the transition id).

## Discovering exact schemas

Jira Cloud API is versioned and the write endpoints differ from the docs you
remember. Pull the authoritative OpenAPI spec and introspect it:
```bash
curl -s "https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json" -o /tmp/jira.json
```
Then walk `paths` → `components.schemas` for the exact request shape (required
fields, enums, `$ref` nesting). This is how you find that `scope` is top-level and
that `statusCategory` is `TODO/IN_PROGRESS/DONE`.

## Pitfalls

- **405 Method Not Allowed** on `/rest/api/2/status`, `/rest/api/2/workflow`,
  `/rest/api/3/workflow`, `/rest/api/3/status` → the write endpoint lives at the
  **plural** api/3 paths (`/rest/api/3/statuses`, `/rest/api/3/workflows/create`).
- **Board creation: try the API token first — it may work.** `POST /rest/agile/1.0/board`
  with `{"name":...,"type":"kanban","filterId":<id>}` CAN succeed with basic-auth API token
  (created board id 34 this way). You must create a saved filter first to get a `filterId`:
  `POST /rest/api/3/filter` with `{"name","jql","favourite":true}` → `.id`. If the POST
  board instead returns `"Client must be authenticated to access this resource."`, fall
  back to OAuth/UI. **Board column configuration cannot be changed via API**:
  `PUT|POST /rest/agile/1.0/board/{id}/configuration` returns **405** (GET works). Board
  columns are derived from the project **workflow** statuses — to get custom columns (e.g.
  per agent role), create a workflow with those statuses and assign it via the workflow
  scheme, then the board reflects them. Don't burn time retrying the board-configuration
  write endpoint.
- **"We couldn't find project N in this scope"** → wrong scope type; use `GLOBAL`
  for company-managed.
- **"Invalid request payload"** → check the swagger schema; likely a misplaced field
  (e.g. `scope` inside each status instead of top-level) or a wrong enum value.
- **`statuses : must not be empty`** on workflow create → the TOP-LEVEL `statuses`
  array is required even when the statuses already exist.
- **`Status name "X" already in use`** on workflow create → the top-level `statuses`
  entry is missing the numeric `id` field, so Jira tries to CREATE a new status instead
  of referencing the existing one. Fix: add `"id":"<numeric-id>"` to each top-level
  `statuses` entry (and use an invented UUID as `statusReference`).
- **`We couldn't find project N in this scope`** on status create → wrong scope type;
  use `GLOBAL` for company-managed, `PROJECT`+`project.id` for team-managed.
- **`Issue type with ID X is missing the mappings required for statuses with IDs Y,Z`**
  on scheme publish → supply `statusMappings` mapping those old statuses to new ones for
  that issue type.
- **`redundant mappings for statuses with IDs X`** on scheme publish → remove any
  mapping where old status == new status (e.g. Done→Done is automatic).
- Free/limited plans restrict some write APIs; check `/rest/api/2/mypermissions?permissions=...`
  if unsure.

## Support files

- `references/jira-workflow-example.md` — a full worked example (project + statuses +
  workflow for a 7-stage release pipeline).
- `scripts/jira.sh` — generic REST helper (GET/POST/PUT/DELETE + JQL search). Point
  `JIRA_CREDS` at an env file with `JIRA_BASE`/`JIRA_EMAIL`/`JIRA_TOKEN` (chmod 600).
