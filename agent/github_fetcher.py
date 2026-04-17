import httpx
from datetime import date, timedelta
from config import GITHUB_TOKEN, GITHUB_USERNAME

GITHUB_API = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _get(url: str, params: dict = None):
    response = httpx.get(url, headers=HEADERS, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _fetch_commits_on(target_date: str) -> list:
    data = _get(f"{GITHUB_API}/search/commits", params={
        "q": f"author:{GITHUB_USERNAME} author-date:{target_date}",
        "per_page": 20,
        "sort": "author-date",
    })
    commits = []
    for item in data.get("items", []):
        commits.append({
            "repo": item["repository"]["full_name"],
            "message": item["commit"]["message"].split("\n")[0],
            "url": item["html_url"],
        })
    return commits


def _fetch_prs_on(target_date: str) -> list:
    data = _get(f"{GITHUB_API}/search/issues", params={
        "q": f"type:pr author:{GITHUB_USERNAME} updated:{target_date}",
        "per_page": 10,
    })
    prs = []
    for item in data.get("items", []):
        prs.append({
            "title": item["title"],
            "repo": item["repository_url"].split("/repos/")[-1],
            "state": item["state"],
            "url": item["html_url"],
        })
    return prs


def fetch_yesterday_activity() -> dict:
    yesterday = str(date.today() - timedelta(days=1))
    try:
        commits = _fetch_commits_on(yesterday)
    except Exception:
        commits = []
    try:
        prs = _fetch_prs_on(yesterday)
    except Exception:
        prs = []
    return {"commits": commits, "prs": prs, "date": yesterday}


def fetch_today_activity() -> dict:
    today = str(date.today())
    try:
        commits = _fetch_commits_on(today)
    except Exception:
        commits = []
    try:
        prs = _fetch_prs_on(today)
    except Exception:
        prs = []
    return {"commits": commits, "prs": prs, "date": today}


def activity_to_text(activity: dict) -> str:
    lines = []
    for c in activity["commits"]:
        lines.append(f"Commit [{c['repo']}]: {c['message']}")
    for pr in activity["prs"]:
        lines.append(f"PR ({pr['state']}) [{pr['repo']}]: {pr['title']}")
    return "\n".join(lines)


def is_github_configured() -> bool:
    return bool(GITHUB_TOKEN and GITHUB_TOKEN != "your_github_token_here"
                and GITHUB_USERNAME and GITHUB_USERNAME != "your_github_username_here")
