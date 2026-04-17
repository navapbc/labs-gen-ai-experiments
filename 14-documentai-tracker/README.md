# Experiment 14: DocumentAI tracker

Automated change-tracking for the DocumentAI workstream in the navapbc GitHub Projects v2 board (Strata, project #4). On a schedule, it:

1. Pulls every item labeled `DocumentAI` (or with `Product Category = DocumentAI`) from navapbc/projects/4 via the GitHub GraphQL API.
2. Diffs against the previous run to detect completions, new items, status transitions, field changes, and assignee shuffles.
3. Writes a PM-oriented email body + a full Claude-Project context doc as artifacts.
4. A scheduled Claude Code agent reads those artifacts and:
   - Creates a Gmail **draft** addressed to Brandon (review before send).
   - Uploads the context doc to Google Drive as a fresh dated Google Doc.

The Python CLI has no MCP/auth dependencies — it just reads GitHub via the user's `gh` CLI and writes artifacts. The Claude agent prompt in [`agent_prompt.md`](agent_prompt.md) handles the notifications.

## Setup

### 1. GitHub scope refresh (one-time)

The default `gh` token is missing the `read:project` scope required for Projects v2. Run:

```bash
gh auth refresh -s read:project
```

Verify with:

```bash
gh api graphql -f query='query { organization(login: "navapbc") { projectV2(number: 4) { title } } }'
```

It should print `{"data":{"organization":{"projectV2":{"title":"Strata"}}}}` (or whatever the project is titled).

### 2. Python deps

```bash
cd 14-documentai-tracker
pip install -r requirements.txt
```

Only `python-dotenv` is pinned. The script uses the standard library otherwise.

### 3. First run

```bash
python -m src.main
```

This writes:

- `artifacts/email_subject.txt`
- `artifacts/email_body.md`
- `artifacts/context.md`  ← the Claude Project knowledge doc
- `artifacts/changes.json`
- `artifacts/summary.json`
- `state/last_snapshot.json`  ← committed so the next run can diff

On the first run, `summary.json.has_email` is `true` (the email is labeled as a baseline). Every subsequent run only sets `has_email=true` when there are meaningful changes.

Add `--dry-run` to skip persisting the new baseline.

### 4. Google Docs destination — two options

Only relevant once you want the context doc in Drive automatically.

- **Option A — Drive MCP, fresh doc each run (simpler, already authenticated).** The Drive MCP in this session has `create_file` but no "update existing file" method. Each run uploads a new dated doc to Drive root. The Claude Project knowledge base would point at the Drive folder or pick the newest doc. No OAuth setup needed.
- **Option B — Google Docs API with OAuth (stable URL).** Authorize a Desktop OAuth client once; the script can then overwrite the existing doc at `docs.google.com/document/d/1RJE023iO8sOPzA0RdntTHV-qoqQXURRnNyhFNQJk0J4/edit` in place on every run. Setup steps live in the chat history / handoff. Drop `credentials.json` in `credentials/`. This isn't wired into the Python yet — ask Claude to add it after `credentials.json` lands.

The agent prompt as written uses **Option A**.

### 5. Schedule it

From a Claude Code session, ask Claude to call `mcp__scheduled-tasks__create_scheduled_task` with:

- `taskId`: `documentai-tracker`
- `description`: `Daily DocumentAI workstream sync — draft email + upload context doc`
- `cronExpression`: `57 8 * * 1-5` (weekdays at 8:57am local — off-minute on purpose)
- `prompt`: contents of [`agent_prompt.md`](agent_prompt.md)
- `notifyOnCompletion`: `true`

The task stores itself at `~/.claude/scheduled-tasks/documentai-tracker/SKILL.md` and spawns a Claude session each fire. It does NOT require an active REPL — it launches when the trigger fires.

## Architecture

```
src/
├── fetch.py    # GraphQL query via `gh api graphql`, normalizes project items
├── state.py    # load/save last_snapshot.json
├── diff.py     # compute_changes(prev, curr) -> list[Change]
├── report.py   # build_email_body + build_context_doc
└── main.py     # orchestrator; writes artifacts; updates baseline
```

The Python code is deliberately free of any MCP, OAuth, SMTP, or credential handling. All side effects (email draft, Drive upload, git commit) are performed by the Claude agent that reads the artifacts — this way auth lives in your Claude Code session and the Python script is trivially testable in isolation.

## What counts as "changed"?

`diff.py` emits these event kinds:

- `new` — an item appeared in the project that wasn't in the last snapshot
- `closed` — item transitioned OPEN → CLOSED (with `state_reason` — COMPLETED / NOT_PLANNED / DUPLICATE)
- `reopened` — item transitioned CLOSED → OPEN
- `field` — any of: Status, Priority, Size, Start date, Target date changed value
- `assignees` — someone added or removed

Add more tracked fields in `diff.py::TRACKED_FIELDS`.

## Limits / known rough edges

- Sub-issues are sourced from the `trackedIssues` connection, which reflects the epic's internal task list. If the Strata board uses a different linking convention, some sub-issues will be missed — check the first email against the actual board and adjust the query in `src/fetch.py::PROJECT_QUERY` if needed.
- The `DocumentAI` filter checks both labels and a custom `Product Category` field. If the board renames that field, `is_documentai_item` in `fetch.py` needs the new field name.
- The snapshot is committed to the repo on each run. If you'd rather keep it out of git history, move it to a Gist or ignore it in `.gitignore` and switch to a durable path outside the repo.
