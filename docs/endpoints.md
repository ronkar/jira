# Jira Cloud REST — Endpoint Reference (verified working)

All endpoints use **Basic auth** (`Authorization: Basic base64(email:api_token)`).
Base URL: `https://<site>.atlassian.net` (here `ronkarny5547.atlassian.net`).

## Auth
```
Basic base64("email:api_token")   # token from id.atlassian.com/manage-profile/security/api-tokens
```

---

## Projects
| Action | Endpoint | Notes |
|--------|----------|-------|
| List | `GET /rest/api/3/project/search` | |
| Create (company-managed) | `POST /rest/api/3/project` | body `{"key","name","projectTypeKey":"software","leadAccountId"}` |
| Delete | `DELETE /rest/api/3/project/{key}` | |
| Get (check style) | `GET /rest/api/3/project/{key}` | `style: next-gen`=team-managed, `classic`=company-managed |

## Statuses
| Action | Endpoint | Notes |
|--------|----------|-------|
| Search | `GET /rest/api/3/statuses/search?maxResults=200` | **plural** `/statuses/search` (singular `/status/search` → 404) |
| Create | `POST /rest/api/3/statuses` | `statusCategory` = `TODO`/`IN_PROGRESS`/`DONE` (uppercase) |

## Workflows
| Action | Endpoint | Notes |
|--------|----------|-------|
| List | `GET /rest/api/3/workflow/search` | |
| **Create** | **`POST /rest/api/3/workflows/create`** | plural + `/create`; see payload below |

Workflow create payload (GLOBAL scope, company-managed):
```json
{
  "scope": {"type": "GLOBAL"},
  "statuses": [
    {"name": "Backlog", "statusCategory": "TODO", "statusReference": "<uuid-or-id>"},
    {"name": "Done", "statusCategory": "DONE", "statusReference": "<uuid-or-id>"}
  ],
  "workflows": [{
    "name": "My Workflow v1",
    "description": "...",
    "statuses": [{"statusReference": "<ref>", "properties": {}}],
    "transitions": [
      {"id": "1", "name": "Create", "type": "INITIAL", "toStatusReference": "<ref>", "links": []},
      {"id": "2", "name": "To Next", "type": "DIRECTED", "toStatusReference": "<ref>",
       "links": [{"fromStatusReference": "<ref>"}]},
      {"id": "8", "name": "Close", "type": "GLOBAL", "toStatusReference": "<ref>", "links": []}
    ]
  }]
}
```
- Transition `id` **must be numeric strings**.
- To reuse an existing GLOBAL status: pass `{"id":"<sid>","name":"...","statusCategory":"...","statusReference":"<sid>"}`.

## Workflow schemes
| Action | Endpoint | Notes |
|--------|----------|-------|
| Create | `POST /rest/api/3/workflowscheme` | body `{"name","defaultWorkflow":"<WorkflowName>"}` |
| Assign to project | `PUT /rest/api/3/workflowscheme/project` | body `{"projectId","workflowSchemeId"}` → **204** = success. Project must be EMPTY. |

## Filters
| Action | Endpoint | Notes |
|--------|----------|-------|
| Create | `POST /rest/api/3/filter` | body `{"name","jql":"project = X ORDER BY created DESC","favourite":true}` |

## Boards (Agile API)
| Action | Endpoint | Notes |
|--------|----------|-------|
| List | `GET /rest/agile/1.0/board` | |
| **Create** | `POST /rest/agile/1.0/board` | **MUST include `location`** (see below) |
| Get | `GET /rest/agile/1.0/board/{id}` | confirm `location` present |
| Delete | `DELETE /rest/agile/1.0/board/{id}` | |
| Config | `GET /rest/agile/1.0/board/{id}/configuration` | read-only (PUT → 405) |
| Issues | `GET /rest/agile/1.0/board/{id}/issue` | |

Board create — **the `location` is critical**:
```json
{"name":"X","type":"kanban","filterId":<id>,"location":{"projectKeyOrId":"<KEY>","type":"project"}}
```

## Board columns (undocumented greenhopper API) — WORKS
| Action | Endpoint | Notes |
|--------|----------|-------|
| Read config | `GET /rest/greenhopper/1.0/rapidviewconfig/editmodel.json?rapidViewId={id}` | what the UI loads for Configure→Columns |
| **Set columns** | **`PUT /rest/greenhopper/1.0/rapidviewconfig/columns`** | body below; verify by re-GET |

```json
{"rapidViewId": 233, "mappedColumns": [
  {"name": "Backlog", "mappedStatuses": [{"id": "10098"}]},
  {"name": "Done",    "mappedStatuses": [{"id": "10005"}]}
]}
```
- `mappedStatuses[].id` = **status id** (from `GET /rest/api/3/statuses/search`).
- Returns 200 + updated config. **Always re-GET editmodel.json to verify actual change.**
- Kanban boards show an extra empty "Backlog" plan column (`isKanPlanColumn:true`) — normal.

## Issues
| Action | Endpoint | Notes |
|--------|----------|-------|
| Create | `POST /rest/api/3/issue` | body `{"fields":{"project":{"key"},"summary","issuetype":{"name":"Task"}}}` |
| Get status | `GET /rest/api/3/issue/{key}?fields=status` | |
| Transitions | `GET /rest/api/3/issue/{key}/transitions` | |
| Search | `POST /rest/api/3/search/jql` | body `{"jql":"...","maxResults":50}` |

---

## Known limitations (can't be changed via API)
- Sidebar color, card layout/design, custom theme colors.
- Board columns via the OFFICIAL API (use the greenhopper endpoint instead).
- Deleting issues: no permission for some.
