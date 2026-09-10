---
name: jira-dynamic-workflow
description: "Use when setting up a new Jira project/board/workflow."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [jira, atlassian, workflow, board, project, agent]
    category: productivity
---

# Dynamic Jira Workflow Agent

Manage Jira Cloud for the user (`ronkarny5547.atlassian.net`). When the user describes a NEW business need (dev project, data analysis, marketing campaign, research, etc.) — do NOT use one fixed template. Instead:

1. Identify the domain/goal from the free-form request.
2. Derive the natural role/persona chain (stages) for that workflow.
3. Build a workflow, statuses, board and project in Jira that match that process exactly.
4. If the goal is unclear — STOP and ask focused clarifying questions. Never guess/invent a process.

## Step 1 — Analyze the request
For a request like "I have project X I want to build/set up", analyze:
- What is the work domain? (software dev, data/BI, marketing, research, design, ops, legal, recruiting, etc.)
- Who are the natural roles in this process? (e.g. dev → PM, Architect, Developer, QA, Security; data → requestor/stakeholder, Data Engineer, Data Analyst, data QA, approver)
- What stages does a work item (issue) pass through from open to close?
- Are there review/approval gates that should be separate statuses?

## Decision rules
- If the request has a clear process description (even if not fully detailed) → build an initial workflow PROPOSAL and present it to the user BEFORE creating anything.
- If the request is too generic / missing critical info (e.g. "set up a project" with no context) → do NOT create. Stop and ask.

## Step 2 — When to ask clarifying questions
Ask ONLY when critical info is missing (max 3-4 focused questions at once). Examples:
- Project goal: "What is the final goal — what should come out of it?"
- Roles: "Which roles/people are involved? (who requests, who does, who reviews/approves)"
- Process stages: "How does a work item move between stages? Is there a review/approval before closing?"
- Existing structure: "Is there a similar process in another project we can base this on, or start from scratch?"
Do NOT invent roles that weren't requested, and do NOT skip a critical question just to speed things up.

## Step 3 — Domain → Workflow reference table
Use as a reasoning base, but ALWAYS adapt to the user's actual details:
| Domain | Example workflow statuses |
|--------|---------------------------|
| Software dev | Backlog → PM Definition → Architecture Design → Development → QA Testing → Security Review → Done |
| Data analysis / BI | Request → Data Sourcing → Data Engineering → Analysis → Review/QA → Insights Delivered |
| Marketing/campaign | Idea → Content Draft → Design → Approval → Scheduled → Live → Retrospective |
| Research | Research Question → Literature/Data Collection → Analysis → Peer Review → Published |
| Ops/support | New → Triage → In Progress → Waiting on Customer → Resolved → Closed |

IMPORTANT: this is only a starting point. If the user has a different process — THEIR process wins.

## Step 4 — Check for an existing board FIRST (before creating anything)
The agent used to create a brand-new project+board for every request, even small one-off ones
(e.g. a single Kafka issue investigation) — causing project sprawl. FIX: before ANY creation
(API/project/workflow), STOP and check for a suitable existing board.

1. **Search existing boards/projects** (the agent already has API access): scan the current
   projects/boards and check whether any board's workflow/category is substantively close to the
   new request. E.g. a "production incident" request → check if a Support/Incident board already exists.
2. **If a close board is found — ASK the user, never decide alone.** Present a clear two-option
   question and WAIT for an explicit answer:
   - "מצאתי board קיים ({project/board name}) שנראה מתאים. איך תרצה להמשיך?"
     - א) להשתמש ב-board הקיים ולהוסיף את זה כ-issue חדש בתוכו
     - ב) זה פרויקט גדול/חדש בפני עצמו — ליצור board נפרד ייעודי
   The agent may add a short recommendation (e.g. "אני ממליץ להשתמש בקיים כי זו תקלה נקודתית"),
   but the FINAL decision is always the user's.
3. **Act on the choice:**
   - User chose "use existing" → create a new ISSUE in the existing board (title, description,
     initial status). Do NOT touch the existing workflow/project structure.
   - User chose "new project" → continue the normal dynamic-workflow process (analysis → approval → create → split columns).
4. **If NO close board exists** (entirely new category) → proceed directly to the normal dynamic
   workflow creation, WITHOUT asking this question (nothing to compare against).

GOLDEN RULE: never decide between "use existing" vs "create new" yourself when a reasonable match
exists — always ask the user. You may recommend, but the user decides.

## Step 5 — Planning: focused clarifying questions BEFORE creating the issue
The agent used to jump straight to creating an issue with just a title (e.g. "Investigate RabbitMQ
issue") without gathering the details actually needed to work the task. FIX: after the board decision
(existing OR new), and BEFORE the API call that creates the issue, run a focused Planning step.
This is MANDATORY, even when the task looks "simple".

**How to ask — not a long interrogation:**
- 3-5 focused questions per task type (see table below), not a generic laundry list.
- Ask 1-2 questions per turn, not all at once if it feels like a form.
- If the user already gave some info in the original request — do NOT re-ask; only fill the gaps.
- If the user answers "don't know"/"check yourself" — it's fine to proceed without it and mark it
  **TBD** in the issue description; don't block the process.

**Domain → Planning questions:**
| Domain | Key questions before creating the issue |
|--------|------------------------------------------|
| Incident / investigation | Which servers/services affected? What exactly is the symptom (error, lag, crash)? When did it start? Impact severity (fully down / limited / cosmetic)? Are logs/metrics available? Any suspected cause (recent deploy, config change)? |
| Feature / software dev | Language/stack? Exact scope (in/out)? Acceptance criteria? Dependencies on other systems/teams? Deadline? |
| Data analysis | Data source? Business question to answer? Relevant time range? Desired output format (report, dashboard, number)? |
| Maintenance / DevOps | Which system/service? One-off or recurring (cron)? Allowed maintenance window? Risk of downtime? |
| Unknown domain | First ask "what exactly is the end goal?" then derive 2-3 follow-up questions (who's involved, input/output, what defines success). |

**What to do with the answers:**
- Put ALL answers into the issue **description** in a structured, readable way (not just the title),
  so anyone opening the issue understands the full context without going back to the agent.
- If the project has relevant custom fields (e.g. "affected server", "component") — map answers to
  those fields instead of free text when possible.
- If some answers affect the chosen persona/workflow itself (e.g. "this isn't just Kafka, it's a
  cross-service failure") — re-confirm with the user that the chosen board still fits, BEFORE creating the issue.

## Step 6 — Split into Subtasks by persona (parallel vs serial)
Until now every request created ONE issue that moves serially through statuses (New → ... → Closed).
That's correct when stages depend on each other, but sometimes a task has several INDEPENDENT parts that
can/should run in parallel — then split into subtasks instead of cramming everything into one description.

**When to split (after Planning):** are there at least two independent parts requiring substantively
different knowledge/persona, with NO hard dependency between them for execution?
- Yes → split into subtasks (structure below).
- No, it's a single serial stream (stage must finish before next) → one normal issue, as before.
  This is still the common case — don't force a split.

**Don't over-split:** only split when it gives real value (separate tracking, actual parallel work).
Don't break a small task into crumbs just because it's technically possible. If in doubt — ASK the user:
"יש כאן כמה חלקים שיכולים לרוץ במקביל ({brief}) — לפצל ל-subtasks נפרדים, או להשאיר כ-issue אחד?"

**Structure in Jira: Parent Issue + Subtasks**
- The original issue stays as ONE parent issue (holds the general context).
- Each independent part becomes a **subtask** under the parent (issue type = Sub-task).
- Each subtask gets:
  - a persona/role — via Assignee if there's a concrete person, or via label/component if still
    planning (e.g. `persona:backend-developer`, `persona:security-review`).
  - its own status from the same workflow (or a relevant subset).
  - a focused description: only the part relevant to it from the Planning info.

**Example — dev task with parallel parts:**
- Parent: "פיתוח מודול ניהול שרתים"
  - Subtask 1 → persona Backend Developer → "בניית API ל-CRUD שרתים"
  - Subtask 2 → persona Frontend Developer → "בניית דשבורד תצוגה" (parallel to 1 if API contract agreed)
  - Subtask 3 → persona Security Review → depends on 1+2, stays serial after them

**Example — incident with parallel parts:**
- Parent: "חקירת RabbitMQ lag"
  - Subtask 1 → "בדיקת לוגים שרת production-3"
  - Subtask 2 → "בדיקת לוגים שרת production-7" (parallel, converge at shared Root Cause)

**What NOT to do:**
- Don't create fully disconnected issues (no parent-subtask link) — loses shared context.
- Don't split a serial stream into subtasks just to "look tidy" — if step B must wait for A, keep it
  as internal description in one issue/subtask.
- Don't decide alone when in doubt — ask the user.

## Step 7 — Approval before creating
Before opening a new project/board/workflow in Jira, present a short summary:
- Proposed project name
- List of statuses/stages
- List of roles (personas) that will appear on the board
Then ask explicit approval: "לאשר יצירה עם המבנה הזה?" Only after approval → proceed to technical execution.

## Step 8 — Technical execution in Jira
- Use the **`jira-cloud-boards`** skill for creating boards/workflows/statuses, INCLUDING the critical `location` parameter (learned from broken boards 34/101 — always ensure a valid location before finishing).
- Use the **`jira-cloud-api`** skill for general operations (projects, schemes, assignments).
- Use `scripts/setup_team_board.py` (from jira-cloud-boards) as the base, and adapt the status/workflow parameters to what was agreed with the user in Step 5.
- After creating the board, **split the columns automatically** (no manual step) using `scripts/set_columns.py <boardId> "ColName:StatusId" ...` from jira-cloud-boards — this uses the undocumented greenhopper API and verifies via re-GET.
- At the end verify: the board renders correctly, has a valid `location`, and ALL agreed statuses appear as their own columns.

## Step 9 — Completion report
At the end report to the user:
- Direct link to the new board
- List of created statuses
- Note if any manual action is still needed (permissions, assigning people to roles, etc.)

## Golden rules
- Do NOT build a generic "default" workflow if the user described a specific process — always customize.
- Ask before guessing when critical info is missing, not before every small thing.
- Get user approval on the proposed workflow structure BEFORE creating anything in Jira.
- Stay technically consistent: ensure a valid board `location` to avoid the broken-board problem (34/101).
- Document each new workflow with a clear goal-identifying name (e.g. "Data Analysis Workflow v1", not just "Team Task Workflow").
