"""Fetch DocumentAI items from navapbc/projects/4 via the GitHub Projects v2 GraphQL API.

Uses `gh api graphql` as a transport so authentication is inherited from the user's
gh CLI (no PAT handling in this module). The gh token must have the `read:project`
scope — run `gh auth refresh -s read:project` once if it doesn't.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any

PROJECT_QUERY = """
query($owner: String!, $number: Int!, $cursor: String) {
  organization(login: $owner) {
    projectV2(number: $number) {
      title
      items(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          type
          content {
            __typename
            ... on Issue {
              number
              title
              url
              state
              stateReason
              createdAt
              updatedAt
              closedAt
              issueType { name }
              repository { nameWithOwner }
              labels(first: 30) { nodes { name } }
              assignees(first: 10) { nodes { login } }
              parent { number title url }
              milestone { title }
              subIssues(first: 50) {
                totalCount
                nodes { number title url state }
              }
              subIssuesSummary { total completed percentCompleted }
            }
            ... on PullRequest {
              number
              title
              url
              state
              repository { nameWithOwner }
            }
            ... on DraftIssue {
              title
            }
          }
          fieldValues(first: 30) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2SingleSelectField { name } }
              }
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2Field { name } }
              }
              ... on ProjectV2ItemFieldNumberValue {
                number
                field { ... on ProjectV2Field { name } }
              }
              ... on ProjectV2ItemFieldDateValue {
                date
                field { ... on ProjectV2Field { name } }
              }
              ... on ProjectV2ItemFieldIterationValue {
                title
                field { ... on ProjectV2IterationField { name } }
              }
              ... on ProjectV2ItemFieldLabelValue {
                labels(first: 20) { nodes { name } }
                field { ... on ProjectV2Field { name } }
              }
            }
          }
        }
      }
    }
  }
}
"""


@dataclass
class ProjectItem:
    """One item (issue/PR/draft) in the project, with DocumentAI-relevant fields flattened."""

    item_id: str
    item_type: str
    number: int | None
    title: str
    url: str | None
    repo: str | None
    state: str | None  # OPEN | CLOSED
    state_reason: str | None  # COMPLETED | NOT_PLANNED | REOPENED
    issue_type: str | None = None  # GitHub native Issue Type (e.g. "Epic")
    labels: list[str] = field(default_factory=list)
    assignees: list[str] = field(default_factory=list)
    parent_number: int | None = None
    parent_title: str | None = None
    milestone: str | None = None
    sub_issues: list[dict[str, Any]] = field(default_factory=list)
    sub_issues_total: int = 0
    sub_issues_completed: int = 0
    sub_issues_percent: int = 0
    created_at: str | None = None
    updated_at: str | None = None
    closed_at: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "number": self.number,
            "title": self.title,
            "url": self.url,
            "repo": self.repo,
            "state": self.state,
            "state_reason": self.state_reason,
            "issue_type": self.issue_type,
            "labels": self.labels,
            "assignees": self.assignees,
            "parent_number": self.parent_number,
            "parent_title": self.parent_title,
            "milestone": self.milestone,
            "sub_issues": self.sub_issues,
            "sub_issues_total": self.sub_issues_total,
            "sub_issues_completed": self.sub_issues_completed,
            "sub_issues_percent": self.sub_issues_percent,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
            "fields": self.fields,
        }


def _run_gh_graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    """Execute a GraphQL query via `gh api graphql`. Returns the parsed `data` object."""
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is None:
            continue
        if isinstance(value, int):
            cmd.extend(["-F", f"{key}={value}"])
        else:
            cmd.extend(["-f", f"{key}={value}"])

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"gh api graphql failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    payload = json.loads(result.stdout)
    if "errors" in payload:
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


def _flatten_field_values(field_values_nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Collapse fieldValues into a flat {field_name: value} dict."""
    out: dict[str, Any] = {}
    for node in field_values_nodes:
        fld = node.get("field") or {}
        name = fld.get("name")
        if not name:
            continue
        tn = node.get("__typename", "")
        if tn == "ProjectV2ItemFieldSingleSelectValue":
            out[name] = node.get("name")
        elif tn == "ProjectV2ItemFieldTextValue":
            out[name] = node.get("text")
        elif tn == "ProjectV2ItemFieldNumberValue":
            out[name] = node.get("number")
        elif tn == "ProjectV2ItemFieldDateValue":
            out[name] = node.get("date")
        elif tn == "ProjectV2ItemFieldIterationValue":
            out[name] = node.get("title")
        elif tn == "ProjectV2ItemFieldLabelValue":
            out[name] = [lbl.get("name") for lbl in node.get("labels", {}).get("nodes", [])]
    return out


def _node_to_item(node: dict[str, Any]) -> ProjectItem | None:
    content = node.get("content") or {}
    tn = content.get("__typename", "")
    fields = _flatten_field_values(node.get("fieldValues", {}).get("nodes", []))

    if tn == "Issue":
        sub_issues_nodes = (content.get("subIssues") or {}).get("nodes", []) or []
        summary = content.get("subIssuesSummary") or {}
        return ProjectItem(
            item_id=node["id"],
            item_type="Issue",
            number=content.get("number"),
            title=content.get("title", ""),
            url=content.get("url"),
            repo=(content.get("repository") or {}).get("nameWithOwner"),
            state=content.get("state"),
            state_reason=content.get("stateReason"),
            issue_type=(content.get("issueType") or {}).get("name"),
            labels=[lbl["name"] for lbl in (content.get("labels") or {}).get("nodes", [])],
            assignees=[a["login"] for a in (content.get("assignees") or {}).get("nodes", [])],
            parent_number=(content.get("parent") or {}).get("number"),
            parent_title=(content.get("parent") or {}).get("title"),
            milestone=(content.get("milestone") or {}).get("title"),
            sub_issues=[
                {"number": s["number"], "title": s["title"], "url": s["url"], "state": s["state"]}
                for s in sub_issues_nodes
            ],
            sub_issues_total=summary.get("total") or (content.get("subIssues") or {}).get("totalCount", 0),
            sub_issues_completed=summary.get("completed", 0),
            sub_issues_percent=summary.get("percentCompleted", 0),
            created_at=content.get("createdAt"),
            updated_at=content.get("updatedAt"),
            closed_at=content.get("closedAt"),
            fields=fields,
        )
    if tn == "PullRequest":
        return ProjectItem(
            item_id=node["id"],
            item_type="PullRequest",
            number=content.get("number"),
            title=content.get("title", ""),
            url=content.get("url"),
            repo=(content.get("repository") or {}).get("nameWithOwner"),
            state=content.get("state"),
            state_reason=None,
            fields=fields,
        )
    if tn == "DraftIssue":
        return ProjectItem(
            item_id=node["id"],
            item_type="DraftIssue",
            number=None,
            title=content.get("title", ""),
            url=None,
            repo=None,
            state=None,
            state_reason=None,
            fields=fields,
        )
    return None


def is_documentai_item(item: ProjectItem) -> bool:
    """Return True if the item belongs to the DocumentAI workstream.

    The Strata board encodes the workstream in the `Product` single-select field
    (values include "DocumentAI", "Case Management SDK", etc.). We also accept a
    `DocumentAI` label as a fallback in case the board convention changes.
    """
    if any(lbl.lower() == "documentai" for lbl in item.labels):
        return True
    product = item.fields.get("Product")
    if isinstance(product, str) and product.lower() == "documentai":
        return True
    return False


def fetch_documentai_items(owner: str = "navapbc", project_number: int = 4) -> list[ProjectItem]:
    """Fetch all project items and return only those belonging to DocumentAI."""
    all_items: list[ProjectItem] = []
    cursor: str | None = None
    while True:
        data = _run_gh_graphql(
            PROJECT_QUERY,
            {"owner": owner, "number": project_number, "cursor": cursor},
        )
        project = (data.get("organization") or {}).get("projectV2")
        if not project:
            raise RuntimeError(
                f"Project not found: organization={owner!r} number={project_number}. "
                "Verify the gh token has read:project scope."
            )
        items_page = project["items"]
        for node in items_page["nodes"]:
            item = _node_to_item(node)
            if item is not None:
                all_items.append(item)
        page_info = items_page["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]

    return [it for it in all_items if is_documentai_item(it)]


if __name__ == "__main__":
    items = fetch_documentai_items()
    print(f"Found {len(items)} DocumentAI items")
    for it in items:
        print(f"  {it.repo}#{it.number} [{it.fields.get('Status', '?')}] {it.title}")
