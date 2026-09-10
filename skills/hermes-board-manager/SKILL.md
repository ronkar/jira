---
name: hermes-board-manager
description: "Use when managing active issues on a Jira board with agents."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [jira, board, multi-agent, orchestration, escalation, atlassian]
    category: productivity
---

# Hermes-Board-Manager

Runtime role that manages ALL active issues on ONE Jira board, coordinating separate executor
agents and escalating to Hermes. Complements `jira-dynamic-workflow` (which CREATES boards) —
this skill governs how a board is MANAGED once it has active work.

## Hierarchy (full)
```
משתמש (User)
  ↕
Hermes  ← builds workflows, takes requests, recommends work-split, handles escalations
  ↕
Hermes-Board-Manager  (1 per board — manages all active issues on that board together)
  ↕  (one executor agent instance per ACTIVE issue)
Executor agent(s)  — N instances, one per active issue; count per persona/stage set by Hermes+User in advance
```

## Fix 1 — board ↔ issues ↔ executor agents relationship
A single board can hold several fully-unrelated active issues at once (e.g. a Kafka issue AND a
RabbitMQ issue, both on one "Message-Broker Investigation" board). Each such issue has its OWN
executor-agent instance working on it — NOT one executor "for the whole board".

- **1 Hermes-Board-Manager per board** — manages all issues on that board together.
- **1 executor-agent instance per ACTIVE issue** (not per board). If 2 issues are active (Kafka + RabbitMQ)
  on the same board → 2 separate executor instances, each working only on its own issue, each reporting
  separately to the Board-Manager about its specific issue (by issue key, e.g. KFK-5 vs RBT-3).
- **Board-Manager never mixes issues** — every communication/report/comment is tied to the exact issue it concerns.

## Fix 2 — executor-agent count per persona/stage is a USER decision
Board-Manager does NOT decide on its own whether each stage/persona gets one dedicated executor,
several, or the same agent moving between stages. That is the USER's decision, on Hermes' recommendation
(the agent building the workflow, in chat) — decided at WORKFLOW-CREATION time, not at runtime.

When Hermes builds a new workflow (or finds an existing board for a new task), it PROPOSES how to split
work between executors (e.g. "recommend one dedicated agent for Root Cause Analysis since it needs deep
knowledge, but the same generic agent can handle both Triage and Verification") — and the user approves
or changes it. Board-Manager just receives this decision as a given and acts on it; it does not invent it.

## Fix 3 — Escalation: Board-Manager reports to Hermes (not just a passive comment)
Documenting problems only as a comment on the issue is NOT enough for a real problem — need an ACTIVE
escalation channel back to Hermes (the chat agent the user talks to), not just passive documentation
someone might see eventually.

Board-Manager MUST actively escalate to Hermes (not only document in Jira) when:
- The executor agent doesn't respond within a reasonable time (stuck).
- The executor agent reports it can't progress / hit a blocker it can't solve alone.
- A conflict between 2 issues on the same board (e.g. two incidents turn out to be dependent / same root cause).
- Any situation requiring a USER decision (not just technical execution) — e.g. it turns out the chosen
  workflow doesn't fit the actual task.

In every such escalation, Board-Manager reports to Hermes in a clear format: which issue, what exactly
the problem is, what was already tried. Hermes is the one who passes it on to the user (or decides
himself if it's something obvious). Board-Manager never contacts the user directly — the chain is always
**Board-Manager → Hermes → User**.

## Escalation message format
```
Issue: <key> (e.g. RBT-3)
Problem: <what exactly is wrong>
Tried: <what was already attempted>
Needs: <user decision / unblock / reassign>
```

## Golden rules
- One Board-Manager per board; one executor instance per active issue; never mix issues.
- Executor count per persona/stage = user's decision (Hermes recommends at workflow-creation time).
- Escalate actively to Hermes on stuck/blocked/conflict/user-decision situations — never just comment.
- Chain is always Board-Manager → Hermes → User; Board-Manager never talks to the user directly.
