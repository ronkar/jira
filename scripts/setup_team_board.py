#!/usr/bin/env python3
"""Full Jira Cloud team-board setup: project -> workflow -> scheme -> assign -> filter -> board(with location).
Usage: python3 setup_team_board.py "<Project Name>" <KEY> [--lead <accountId>]
Reads creds from /root/jira_cloud/credentials.env. Uses Jira Cloud REST API v3 + Agile API.
"""
import json, os, sys, uuid, urllib.request, base64, urllib.error

NAME = sys.argv[1] if len(sys.argv) > 1 else "Team Task"
KEY = sys.argv[2] if len(sys.argv) > 2 else "TASK"

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

roles = [("Manager","TODO"),("Architect","IN_PROGRESS"),("Developer","IN_PROGRESS"),
         ("Tester","IN_PROGRESS"),("Security Review","IN_PROGRESS"),("PM","DONE")]

# 1. Project (company-managed/classic)
lead = creds.get("JIRA_LEAD", "5b35e5a0349a91633c1bb1a7")
st, proj = req("POST", "/rest/api/3/project",
    {"key": KEY, "name": NAME, "projectTypeKey": "software", "leadAccountId": lead,
     "description": f"{NAME} board project"})
if st not in (200, 201):
    print("PROJECT ERROR", st, proj); sys.exit(1)
project_id = str(proj["id"]); print("project:", KEY, project_id)

# 2. Workflow (GLOBAL scope, reuse existing statuses by name if possible, else create)
# Reuse existing GLOBAL role statuses if they exist (avoid name collision)
_, existing = req("GET", "/rest/api/3/workflow/search?maxResults=100")
sid_map = {}
# find existing statuses by name via /rest/api/3/status/search
_, sts = req("GET", "/rest/api/3/statuses/search?maxResults=200")
for s in sts.get("values", []):
    if s.get("name") in [r[0] for r in roles] and s.get("scope", {}).get("type") == "GLOBAL":
        sid_map[s["name"]] = s["id"]

statuses, wf_statuses, refs = [], [], {}
for name, cat in roles:
    if name in sid_map:  # reuse existing global status
        sid = sid_map[name]
        refs[name] = sid
        statuses.append({"id": sid, "name": name, "statusCategory": cat, "statusReference": sid})
    else:
        ref = str(uuid.uuid4())
        refs[name] = ref
        statuses.append({"name": name, "statusCategory": cat, "statusReference": ref})
    wf_statuses.append({"statusReference": refs[name], "properties": {}})

transitions = [{"id": "1", "name": "Create", "type": "INITIAL", "toStatusReference": refs["Manager"], "links": []}]
for i, (s, d) in enumerate([("Manager","Architect"),("Architect","Developer"),("Developer","Tester"),
                            ("Tester","Security Review"),("Security Review","PM")], start=2):
    transitions.append({"id": str(i), "name": f"To {d}", "type": "DIRECTED",
                        "toStatusReference": refs[d], "links": [{"fromStatusReference": refs[s]}]})
transitions.append({"id": "7", "name": "Close", "type": "GLOBAL", "toStatusReference": refs["PM"], "links": []})
transitions.append({"id": "8", "name": "Reopen", "type": "GLOBAL", "toStatusReference": refs["Manager"], "links": []})

wf_name = f"{NAME} Workflow"
st, wf = req("POST", "/rest/api/3/workflows/create",
    {"scope": {"type": "GLOBAL"}, "statuses": statuses,
     "workflows": [{"name": wf_name, "description": "Agent role workflow",
                    "statuses": wf_statuses, "transitions": transitions}]})
if st not in (200, 201):
    print("WORKFLOW ERROR", st, wf); sys.exit(1)
print("workflow:", wf_name)

# 3. Workflow scheme
st, scheme = req("POST", "/rest/api/3/workflowscheme",
    {"name": f"{NAME} Scheme", "description": "Agent role workflow scheme", "defaultWorkflow": wf_name})
if st not in (200, 201):
    print("SCHEME ERROR", st, scheme); sys.exit(1)
scheme_id = str(scheme["id"]); print("scheme:", scheme_id)

# 4. Assign scheme to project (project must be EMPTY)
st, _ = req("PUT", "/rest/api/3/workflowscheme/project",
    {"projectId": project_id, "workflowSchemeId": scheme_id})
if st not in (200, 204):  # 204 No Content = success
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

# 7. Verify board has location
st, bobj = req("GET", f"/rest/agile/1.0/board/{board_id}")
has_loc = "location" in bobj
print("board location present:", has_loc)
if not has_loc:
    print("WARNING: board has no location -> UI will fail to render. Recreate with location.")
print(f"\nBoard URL: {BASE}/jira/software/projects/{KEY}/boards/{board_id}")
