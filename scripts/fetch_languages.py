"""
Aggregate language byte counts across all non-fork public repos via the
GitHub API and write languages.json (top 5 + "Other"), consumed by
make_hero_svg.py. Run manually, or automatically by
.github/workflows/update-languages.yml on a schedule.
"""
import json
import os
import urllib.request

USER = "ghostmikz"
TOP_N = 5
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "languages.json")

# github/linguist's canonical per-language colors (same ones GitHub's own
# repo language bar uses), so this matches GitHub's own convention.
LINGUIST_COLORS = {
    "Java": "#b07219", "TypeScript": "#3178c6", "CSS": "#563d7c", "HTML": "#e34c26",
    "C++": "#f34b7d", "C": "#555555", "JavaScript": "#f1e05a", "Python": "#3572A5",
    "C#": "#178600", "Shell": "#89e051", "Batchfile": "#C1F12E", "Dockerfile": "#384d54",
}
DEFAULT_COLOR = "#8b949e"


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


repos = []
page = 1
while True:
    batch = api(f"/users/{USER}/repos?per_page=100&page={page}")
    if not batch:
        break
    repos.extend(r["name"] for r in batch if not r["fork"])
    page += 1

totals = {}
for name in repos:
    for lang, n in api(f"/repos/{USER}/{name}/languages").items():
        totals[lang] = totals.get(lang, 0) + n

total_bytes = sum(totals.values())
ranked = sorted(totals.items(), key=lambda kv: -kv[1])
top, rest = ranked[:TOP_N], ranked[TOP_N:]

data = {
    "languages": [
        {"name": lang, "pct": round(100.0 * n / total_bytes, 1), "color": LINGUIST_COLORS.get(lang, DEFAULT_COLOR)}
        for lang, n in top
    ],
    "other_pct": round(100.0 * sum(n for _, n in rest) / total_bytes, 1) if total_bytes else 0.0,
}

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)
print("wrote", OUT, data)
