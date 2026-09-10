#!/usr/bin/env python3
"""Create Kafka Investigation project/board/workflow in Jira Cloud."""
import json, sys, uuid, urllib.request, base64, urllib.error

NAME = "Kafka Investigation"
KEY = "KFK"

creds = {}
for line in open("/root/jira_cloud/credentials.env"):
    line = line.strip()
    if "=" in line:
        k, v = line.split("=", 1)
        creds[k] = v
BASE = creds.get("JIRA_BASE", "https://ronkarny5547.atlassian.net")
AUTH = base64.b64encode(f"{creds['JIRA_EMAIL']}:{creds['JIRA_TOKEN']}".encode()).decode()

def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{BASE}{path}", data=data,
        headers={"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

roles = [
    ("New", "TODO"),
    ("Triage", "IN_PROGRESS"),
    ("Investigation", "IN_PROGRESS"),
    ("Root Cause Identified", "IN_PROGRESS"),
    ("Resolution", "IN_PROGRESS"),
    ("Verification", "IN_PROGRESS"),
    ("Closed", "DONE"),
]

# 1. Project
lead = creds.get("JIRA_LEAD", "5b35e5a0349a91633c1bb1a7")
st, proj = req("POST", "/rest/api/3/project",
    {"key": KEY, "name": NAME, "projectTypeKey": "software", "leadAccountId": lead,
     "description": "Investigate and resolve Kafka issues (triage -> root cause -> resolution -> verify)"})
if st not in (200, 201):
    print("PROJECT ERROR", st, proj); sys.exit(1)
project_id = str(proj["id"]); print("project:", KEY, project_id)

# 2. Workflow (GLOBAL scope, reuse existing GLOBAL statuses by name if present)
_, sts = req("GET", "/rest/api/3/statuses/search?maxResults=200")
sid_map = {}
for s in sts.get("values", []):
    if s.get("name") in [r[0] for r in roles] and s.get("scope", {}).get("type") == "GLOBAL":
        sid_map[s["name"]] = s["id"]

statuses, wf_statuses, refs = [], [], {}
for name, cat in roles:
    if name in sid_map:
        sid = sid_map[name]; refs[name] = sid
        statuses.append({"id": sid, "name": name, "statusCategory": cat, "statusReference": sid})
    else:
        ref = str(uuid.uuid4()); refs[name] = ref
        statuses.append({"name": name, "statusCategory": cat, "statusReference": ref})
    wf_statuses.append({"statusReference": refs[name], "properties": {}})

names = [r[0] for r in roles]
transitions = [{"id": "1", "name": "Create", "type": "INITIAL", "toStatusReference": refs["New"], "links": []}]
for i in range(len(names) - 1):
    transitions.append({"id": str(i + 2), "name": f"To {names[i+1]}", "type": "DIRECTED",
                        "toStatusReference": refs[names[i+1]], "links": [{"fromStatusReference": refs[names[i]]}]})
transitions.append({"id": "8", "name": "Close", "type": "GLOBAL", "toStatusReference": refs["Closed"], "links": []})
transitions.append({"id": "9", "name": "Reopen", "type": "GLOBAL", "toStatusReference": refs["New"], "links": []})

wf_name = "Kafka Investigation Workflow v1"
st, wf = req("POST", "/rest/api/3/workflows/create",
    {"scope": {"type": "GLOBAL"}, "statuses": statuses,
     "workflows": [{"name": wf_name, "description": "Kafka issue investigation workflow",
                    "statuses": wf_statuses, "transitions": transitions}]})
if st not in (200, 201):
    print("WORKFLOW ERROR", st, wf); sys.exit(1)
print("workflow:", wf_name)

# 3. Scheme
st, scheme = req("POST", "/rest/api/3/workflowscheme",
    {"name": f"{NAME} Scheme", "description": "Kafka investigation workflow scheme", "defaultWorkflow": wf_name})
if st not in (200, 201):
    print("SCHEME ERROR", st, scheme); sys.exit(1)
scheme_id = str(scheme["id"]); print("scheme:", scheme_id)

# 4. Assign scheme to project (must be empty)
st, _ = req("PUT", "/rest/api/3/workflowscheme/project",
    {"projectId": project_id, "workflowSchemeId": scheme_id})
if st not in (200, 204):
    print("ASSIGN ERROR", st); sys.exit(1)
print("scheme assigned to", KEY)

# 5. Filter
st, flt = req("POST", "/rest/api/3/filter",
    {"name": f"{NAME} - All", "jql": f"project = {KEY} ORDER BY created DESC", "favourite": True})
if st not in (200, 201):
    print("FILTER ERROR", st, flt); sys.exit(1)
filter_id = flt["id"]; print("filter:", filter_id)

# 6. Board WITH location (CRITICAL)
st, board = req("POST", "/rest/agile/1.0/board",
    {"name": NAME, "type": "kanban", "filterId": filter_id,
     "location": {"projectKeyOrId": KEY, "type": "project"}})
if st not in (200, 201):
    print("BOARD ERROR", st, board); sys.exit(1)
board_id = board["id"]; print("board:", board_id)

# 7. Verify location
st, bobj = req("GET", f"/rest/agile/1.0/board/{board_id}")
has_loc = "location" in bobj
print("board location present:", has_loc)
if not has_loc:
    print("WARNING: no location -> UI will fail to render")
print(f"\nBoard URL: {BASE}/jira/software/projects/{KEY}/boards/{board_id}")
