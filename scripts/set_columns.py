#!/usr/bin/env python3
"""Set board columns via the undocumented greenhopper API (no browser).
Usage: python3 set_columns.py <boardId> "ColumnName:StatusId" ["Col2:Id2" ...]
Example: python3 set_columns.py 233 "Backlog:10098" "PM Definition:10099" "Done:10005"
Reads creds from /root/jira_cloud/credentials.env. Verifies via re-GET after write.
"""
import json, sys, urllib.request, base64, urllib.error

if len(sys.argv) < 3:
    print(__doc__); sys.exit(1)
board_id = sys.argv[1]
cols = []
for arg in sys.argv[2:]:
    name, sid = arg.split(":")
    cols.append({"name": name.strip(), "mappedStatuses": [{"id": sid.strip()}]})

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

payload = {"rapidViewId": int(board_id), "mappedColumns": cols}
st, resp = req("PUT", "/rest/greenhopper/1.0/rapidviewconfig/columns", payload)
print("PUT status:", st)
if st not in (200, 201):
    print("ERROR:", json.dumps(resp, ensure_ascii=False)[:500]); sys.exit(1)

# VERIFY by re-reading editmodel
st2, em = req("GET", f"/rest/greenhopper/1.0/rapidviewconfig/editmodel.json?rapidViewId={board_id}")
if st2 != 200:
    print("VERIFY GET failed:", st2); sys.exit(1)
print("\n=== columns after update ===")
for c in em.get("rapidListConfig", {}).get("mappedColumns", []):
    print(f"  {c['name']!r}: {[s['name'] for s in c.get('mappedStatuses', [])]}")
