import json
import os
import re
import urllib.request

USERNAME = os.environ.get("GH_USERNAME", "SachinK862007")
API_URL = f"https://api.github.com/users/{USERNAME}/events/public"
README_PATH = "README.md"
MAX_ITEMS = 6

# Real GitHub icons — Primer Octicons is GitHub's own official icon library,
# the same set used across github.com itself. Served via Iconify's API instead
# of raw.githubusercontent.com, because raw.githubusercontent.com sends SVGs
# with a text/plain content type, which browsers refuse to render as images —
# that's why icons weren't showing up before. Iconify serves the same icons
# with the correct image/svg+xml type, and lets us bake in a fixed color so
# the icon is visible on both light and dark GitHub themes.
ICON_COLOR = "6e7681"  # neutral gray, readable on both light and dark backgrounds
ICON_BASE = f"https://api.iconify.design/octicon"
ICONS = {
    "push": f"{ICON_BASE}:git-commit-16.svg?color=%23{ICON_COLOR}",
    "pr_open": f"{ICON_BASE}:git-pull-request-16.svg?color=%23{ICON_COLOR}",
    "pr_merge": f"{ICON_BASE}:git-merge-16.svg?color=%23{ICON_COLOR}",
    "issue_open": f"{ICON_BASE}:issue-opened-16.svg?color=%23{ICON_COLOR}",
    "issue_close": f"{ICON_BASE}:issue-closed-16.svg?color=%23{ICON_COLOR}",
    "comment": f"{ICON_BASE}:comment-16.svg?color=%23{ICON_COLOR}",
    "review": f"{ICON_BASE}:eye-16.svg?color=%23{ICON_COLOR}",
    "create": f"{ICON_BASE}:repo-16.svg?color=%23{ICON_COLOR}",
}


def fetch_events():
    headers = {
        "User-Agent": "readme-activity-bot",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API_URL, headers=headers)
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())


def format_event(event):
    repo = event["repo"]["name"]
    repo_url = f"https://github.com/{repo}"
    etype = event["type"]
    payload = event.get("payload", {})

    if etype == "PushEvent":
        commits = payload.get("commits", [])
        head_sha = payload.get("head") or payload.get("after")
        if commits:
            sha = commits[-1]["sha"][:7]
            full_sha = commits[-1]["sha"]
        elif head_sha:
            sha = head_sha[:7]
            full_sha = head_sha
        else:
            return None
        commit_url = f"{repo_url}/commit/{full_sha}"
        return ICONS["push"], f"Pushed commit {sha} to {repo}", commit_url

    if etype == "PullRequestEvent":
        pr = payload.get("pull_request", {})
        number = pr.get("number")
        url = pr.get("html_url", repo_url)
        if payload.get("action") == "closed" and pr.get("merged"):
            return ICONS["pr_merge"], f"Merged PR #{number} in {repo}", url
        if payload.get("action") == "opened":
            return ICONS["pr_open"], f"Opened PR #{number} in {repo}", url
        return None

    if etype == "IssuesEvent":
        issue = payload.get("issue", {})
        number = issue.get("number")
        url = issue.get("html_url", repo_url)
        if payload.get("action") == "opened":
            return ICONS["issue_open"], f"Opened issue #{number} in {repo}", url
        if payload.get("action") == "closed":
            return ICONS["issue_close"], f"Closed issue #{number} in {repo}", url
        return None

    if etype == "IssueCommentEvent":
        issue = payload.get("issue", {})
        number = issue.get("number")
        url = payload.get("comment", {}).get("html_url", issue.get("html_url", repo_url))
        kind = "PR" if "pull_request" in issue else "issue"
        return ICONS["comment"], f"Commented on {kind} #{number} in {repo}", url

    if etype == "PullRequestReviewEvent":
        pr = payload.get("pull_request", {})
        number = pr.get("number")
        url = payload.get("review", {}).get("html_url", pr.get("html_url", repo_url))
        return ICONS["review"], f"Reviewed PR #{number} in {repo}", url

    if etype == "CreateEvent" and payload.get("ref_type") == "repository":
        return ICONS["create"], f"Created repository {repo}", repo_url

    return None


def build_lines(events):
    lines = []
    for event in events:
        formatted = format_event(event)
        if formatted:
            icon, text, url = formatted
            lines.append(
                f'<a href="{url}"><img src="{icon}" width="16" valign="middle"/> {text}</a><br><br>'
            )
        if len(lines) >= MAX_ITEMS:
            break
    if not lines:
        lines.append("No recent public activity found.")
    return "\n".join(lines)


def update_readme(activity_block):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(<!--START_SECTION:activity-->)(.*?)(<!--END_SECTION:activity-->)"
    safe_block = activity_block.replace("\\", "\\\\")
    new_content = re.sub(
        pattern,
        lambda m: f"{m.group(1)}\n{safe_block}\n{m.group(3)}",
        content,
        flags=re.DOTALL,
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    events = fetch_events()
    activity_block = build_lines(events)
    update_readme(activity_block)


if __name__ == "__main__":
    main()
