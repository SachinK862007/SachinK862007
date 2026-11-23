"""Generates assets/stats.svg - a GitHub stats card drawn locally (Night Owl colors).

No third-party card service is used, so it cannot go offline. Numbers come
from GitHub's own API using the workflow's built-in GITHUB_TOKEN.
If anything fails, the existing card is left untouched.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

USERNAME = os.environ.get("GH_USERNAME", "SachinK862007")
DISPLAY_NAME = "Sachin Gowda K"
OUT_PATH = "assets/stats.svg"
API = "https://api.github.com"

# Night Owl palette
BG, BORDER = "#011627", "#1d3b53"
TITLE, TEXT, ICON = "#c792ea", "#7fdbca", "#7fdbca"
FONT = "Segoe UI, Ubuntu, Helvetica, Arial, sans-serif"

ICON_PATHS = {"star": ["M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 .698 0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 1-.564-.41L8 2.694Z"], "git-commit": ["M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.75a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z"], "git-pull-request": ["M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z"], "issue-opened": ["M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z", "M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z"], "repo": ["M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"]}


def api_get(path):
    headers = {"User-Agent": "readme-stats-bot", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode())


def search_count(kind, query):
    q = urllib.parse.quote(query)
    return api_get(f"/search/{kind}?q={q}&per_page=1")["total_count"]


def fetch_stats():
    user = api_get(f"/users/{USERNAME}")
    stars, page = 0, 1
    while True:
        repos = api_get(f"/users/{USERNAME}/repos?per_page=100&page={page}")
        stars += sum(r.get("stargazers_count", 0) for r in repos)
        if len(repos) < 100:
            break
        page += 1
    return [
        ("star", "Total Stars", stars),
        ("git-commit", "Total Commits", search_count("commits", f"author:{USERNAME}")),
        ("git-pull-request", "Total PRs", search_count("issues", f"author:{USERNAME} type:pr")),
        ("issue-opened", "Total Issues", search_count("issues", f"author:{USERNAME} type:issue")),
        ("repo", "Public Repos", user.get("public_repos", 0)),
    ]


def render(rows, name):
    width, row_h, top = 420, 30, 72
    height = top + row_h * (len(rows) - 1) + 30
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub stats">',
        f'<rect x="0.5" y="0.5" rx="8" width="{width - 1}" height="{height - 1}" fill="{BG}" stroke="{BORDER}"/>',
        f'<text x="24" y="40" font-family="{FONT}" font-size="18" font-weight="600" fill="{TITLE}">{name}&#8217;s GitHub Stats</text>',
    ]
    for i, (icon, label, value) in enumerate(rows):
        y = top + i * row_h
        shown = f"{value:,}" if isinstance(value, int) else value
        paths = "".join(f'<path d="{d}"/>' for d in ICON_PATHS[icon])
        out.append(f'<g transform="translate(24,{y - 13})" fill="{ICON}">{paths}</g>')
        out.append(f'<text x="52" y="{y}" font-family="{FONT}" font-size="14" fill="{TEXT}">{label}</text>')
        out.append(f'<text x="{width - 24}" y="{y}" text-anchor="end" font-family="{FONT}" font-size="14" font-weight="600" fill="{TEXT}">{shown}</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    try:
        rows = fetch_stats()
    except Exception as exc:  # keep the existing card if the API fails
        print(f"Stats update skipped: {exc}")
        return 0
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(render(rows, DISPLAY_NAME))
    print("Stats card updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
