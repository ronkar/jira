#!/usr/bin/env python3
"""Create a Jira Cloud workflow with role statuses + transitions.
Usage: python3 create_workflow.py "My Workflow Name" [GLOBAL|PROJECT]
Reads creds from /root/jira_cloud/credentials.env. Uses /rest/api/3/workflows/create.
"""
import json, os, sys, uuid, urllib.request, base64

NAME = sys.argv[1] if len(sys.argv) > 1 else "Team Task Workflow"
SCOPE_TYPE = sys.argv[2] if len(sys.argv) > 2 else "GLOBAL"

# Load creds
creds = {}
for line in open("/root/jira_cloud/credentials.env"):
    line = line.strip()
    if "=" in line:
        k, v = line.split("=", 1)
        creds[k] = v
BASE = creds.get("JIRA_BASE", "https://ronkarny5547.atlassian.net")
auth = base64.b64encode(f"{creds['JIRA_EMAIL']}:{creds['JIRA_TOKEN']}".encode()).decode()

roles = [("Manager","TODO"),("Architect","IN_PROGRESS"),("Developer","IN_PROGRESS"),
         ("Tester","IN_PROGRESS"),("Security Review","IN_PROGRESS"),("PM","DONE")]

# Company-managed -> statusReference = numeric id; team-managed -> UUID.
refs = {}
for name, _ in roles:
    refs[name] = str(uuid.uuid4()) if SCOPE_TYPE == "PROJECT" else str(len(refs) + 100)

statuses = [{"name": n, "statusCategory": c, "statusReference": refs[n]} for n, c in roles]
wf_statuses = [{"statusReference": refs[n], "properties": {}} for n, _ in roles]

transitions = [{"id": "1", "name": "Start", "type": "INITIAL",
                "toStatusReference": refs["Manager"], "links": []}]
for i, (s, d) in enumerate([("Manager","Architect"),("Architect","Developer"),("Developer","Tester"),
                            ("Tester","Security Review"),("Security Review","PM")], start=2):
    transitions.append({"id": str(i), "name": f"To {d}", "type": "DIRECTED",
                        "toStatusReference": refs[d], "links": [{"fromStatusReference": refs[s]}]})

payload = {"scope": {"type": SCOPE_TYPE}, "statuses": statuses,
           "workflows": [{"name": NAME, "description": "Agent role workflow",
                          "statuses": wf_statuses, "transitions": transitions}]}

req = urllib.request.Request(
    f"{BASE}/rest/api/3/workflows/create",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
    method="POST")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("STATUS", r.status)
        print(r.read().decode()[:600])
except urllib.error.HTTPError as e:
    print("ERROR", e.code, e.read().decode()[:600])
