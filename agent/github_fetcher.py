import httpx
from datetime import date
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


def fetch_commits_today() -> list:
    today = str(date.today())
    data = _get(f"{GITHUB_API}/search/commits", params={
        "q": f"author:{GITHUB_USERNAME} author-date:{today}",
        "per_page": 20,
        "sort": "author-date",
    })
    commits = []
    for item in data.get("items", []):
        commits.append({
            "repo": item["repository"]["full_name"],
            "message": item["commit"]["message"].split("\n")[0],  # first line only
            "url": item["html_url"],
        })
    return commits


def fetch_prs_today() -> list:
    today = str(date.today())
    data = _get(f"{GITHUB_API}/search/issues", params={
        "q": f"type:pr author:{GITHUB_USERNAME} updated:{today}",
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


def fetch_github_activity() -> dict:
    try:
        commits = fetch_commits_today()
    except Exception:
        commits = []

    try:
        prs = fetch_prs_today()
    except Exception:
        prs = []

    return {"commits": commits, "prs": prs}


def is_github_configured() -> bool:
    return bool(GITHUB_TOKEN and GITHUB_TOKEN != "your_github_token_here"
                and GITHUB_USERNAME and GITHUB_USERNAME != "your_github_username_here")
