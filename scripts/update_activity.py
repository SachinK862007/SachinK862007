import json
import os
import re
import urllib.request

USERNAME = os.environ.get("GH_USERNAME", "SachinK862007")
API_URL = f"https://api.github.com/users/{USERNAME}/events/public"
README_PATH = "README.md"
MAX_ITEMS = 6

# Icons are GitHub's own Octicons, stored in this repo under assets/icons/,
# so no outside icon service can ever fail or be blocked.
ICON_BASE = "assets/icons"
ICONS = {
    "push": f"{ICON_BASE}/git-commit.svg",
    "pr_open": f"{ICON_BASE}/git-pull-request.svg",
    "pr_merge": f"{ICON_BASE}/git-merge.svg",
    "pr_close": f"{ICON_BASE}/git-pull-request-closed.svg",
    "issue_open": f"{ICON_BASE}/issue-opened.svg",
    "issue_close": f"{ICON_BASE}/issue-closed.svg",
    "comment": f"{ICON_BASE}/comment.svg",
    "review": f"{ICON_BASE}/eye.svg",
    "create": f"{ICON_BASE}/repo.svg",
}


def _headers():
    headers = {
        "User-Agent": "readme-activity-bot",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def api_get(url):
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode())


def fetch_events():
    return api_get(API_URL)


def pr_is_merged(pr):
    """GitHub's event feed no longer includes the merged flag, so ask the PR itself."""
    if "merged" in pr:
        return bool(pr["merged"])
    try:
        return bool(api_get(pr["url"]).get("merged"))
    except Exception:
        return False


def format_event(event):
    repo = event["repo"]["name"]
    repo_url = f"https://github.com/{repo}"
    etype = event["type"]
    payload = event.get("payload", {})

    if etype == "PushEvent":
        commits = payload.get("commits", [])
        head_sha = payload.get("head") or payload.get("after")
        if commits:
            full_sha = commits[-1]["sha"]
        elif head_sha:
            full_sha = head_sha
        else:
            return None
        return (
            ICONS["push"],
            f"Pushed commit {full_sha[:7]} to {repo}",
            f"{repo_url}/commit/{full_sha}",
        )

    if etype == "PullRequestEvent":
        pr = payload.get("pull_request", {})
        number = pr.get("number") or payload.get("number")
        url = f"{repo_url}/pull/{number}"
        action = payload.get("action")
        if action == "opened":
            return ICONS["pr_open"], f"Opened PR #{number} in {repo}", url
        if action == "closed":
            if pr_is_merged(pr):
                return ICONS["pr_merge"], f"Merged PR #{number} in {repo}", url
            return ICONS["pr_close"], f"Closed PR #{number} in {repo}", url
        return None

    if etype == "IssuesEvent":
        issue = payload.get("issue", {})
        number = issue.get("number")
        url = f"{repo_url}/issues/{number}"
        action = payload.get("action")
        if action == "opened":
            return ICONS["issue_open"], f"Opened issue #{number} in {repo}", url
        if action == "closed":
            return ICONS["issue_close"], f"Closed issue #{number} in {repo}", url
        return None

    if etype == "IssueCommentEvent":
        issue = payload.get("issue", {})
        number = issue.get("number")
        comment_id = payload.get("comment", {}).get("id")
        url = f"{repo_url}/issues/{number}"
        if comment_id:
            url += f"#issuecomment-{comment_id}"
        return ICONS["comment"], f"Commented on #{number} in {repo}", url

    if etype == "PullRequestReviewEvent":
        pr = payload.get("pull_request", {})
        number = pr.get("number")
        return ICONS["review"], f"Reviewed PR #{number} in {repo}", f"{repo_url}/pull/{number}"

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
                f'<a href="{url}"><img src="{icon}" width="16" height="16" align="absmiddle"/> {text}</a><br><br>'
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
    new_content = re.sub(
        pattern,
        lambda m: f"{m.group(1)}\n{activity_block}\n{m.group(3)}",
        content,
        flags=re.DOTALL,
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    events = fetch_events()
    update_readme(build_lines(events))


if __name__ == "__main__":
    main()
