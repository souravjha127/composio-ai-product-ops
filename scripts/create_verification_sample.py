import json
import random
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]

with open(ROOT / "data" / "verified_results.json", encoding="utf-8") as f:
    records = json.load(f)

random.seed(42)

# Group by category
by_category = defaultdict(list)

for r in records:
    by_category[r.get("category", "Unknown")].append(r)

sample = []

# Pick 1 app from each category first = 10 apps
for category in sorted(by_category):
    candidates = by_category[category]
    sample.append(random.choice(candidates))

selected_apps = {r["app"] for r in sample}

# Add difficult / interesting cases
priority = [
    r for r in records
    if r["app"] not in selected_apps
    and (
        r.get("verification_status") == "failed"
        or r.get("confidence") == "low"
        or r.get("mcp") == "found"
        or r.get("buildability") in {"blocked", "conditional"}
    )
]

random.shuffle(priority)

for r in priority:
    if len(sample) >= 20:
        break
    sample.append(r)

# If still under 20, fill randomly
remaining = [r for r in records if r["app"] not in {x["app"] for x in sample}]
random.shuffle(remaining)

for r in remaining:
    if len(sample) >= 20:
        break
    sample.append(r)

# Sort for easier manual review
sample.sort(key=lambda x: (x.get("category", ""), x["app"]))

output = []

for i, r in enumerate(sample, 1):
    output.append({
        "sample_id": i,
        "app": r["app"],
        "category": r.get("category"),
        "website": r.get("website"),
        "docs_hint": r.get("docs_hint"),
        "first_pass": {
            "authentication": r.get("original", {}).get("authentication"),
            "credential_access": r.get("original", {}).get("credential_access"),
            "api_surface": r.get("original", {}).get("api_surface"),
            "api_breadth": r.get("original", {}).get("api_breadth"),
            "mcp": r.get("original", {}).get("mcp"),
            "buildability": r.get("original", {}).get("buildability"),
        },
        "verified": {
            "authentication": r.get("authentication"),
            "credential_access": r.get("credential_access"),
            "api_surface": r.get("api_surface"),
            "api_breadth": r.get("api_breadth"),
            "mcp": r.get("mcp"),
            "buildability": r.get("buildability"),
        },
        "verification_status": r.get("verification_status"),
        "human_check": {
            "checked": False,
            "authentication": None,
            "credential_access": None,
            "api_surface": None,
            "api_breadth": None,
            "mcp": None,
            "buildability": None,
            "notes": "",
            "evidence_urls": []
        }
    })

with open(
    ROOT / "data" / "human_verification_sample.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("=" * 60)
print("HUMAN VERIFICATION SAMPLE")
print("=" * 60)
print(f"Sample size: {len(output)}")
print()

for r in output:
    print(
        f"{r['sample_id']:02d}. "
        f"{r['app']} | "
        f"{r['category']} | "
        f"status={r['verification_status']}"
    )

print()
print("Output:")
print(ROOT / "data" / "human_verification_sample.json")