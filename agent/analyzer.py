import json
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "verified_results.json"
HUMAN_INPUT = ROOT / "data" / "human_verification_sample.json"
OUTPUT = ROOT / "data" / "analysis.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def counter_to_dict(counter):
    return dict(counter.most_common())


def main():
    results = load_json(INPUT)
    human = load_json(HUMAN_INPUT)

    # -----------------------------
    # Overall distributions
    # -----------------------------

    auth = Counter()
    access = Counter()
    api_surface = Counter()
    breadth = Counter()
    mcp = Counter()
    buildability = Counter()
    confidence = Counter()
    categories = Counter()

    for r in results:
        categories[r["category"]] += 1
        auth[r.get("authentication", "unknown")] += 1
        access[r.get("credential_access", "unknown")] += 1
        api_surface[r.get("api_surface", "unknown")] += 1
        breadth[r.get("api_breadth", "unknown")] += 1
        mcp[r.get("mcp", "unknown")] += 1
        buildability[r.get("buildability", "unknown")] += 1
        confidence[r.get("confidence", "unknown")] += 1

    # -----------------------------
    # Category-level patterns
    # -----------------------------

    category_stats = defaultdict(lambda: {
        "apps": 0,
        "ready": 0,
        "conditional": 0,
        "blocked": 0,
        "unknown": 0,
        "partner_gated": 0,
        "self_serve": 0,
        "mcp_found": 0,
    })

    for r in results:
        cat = r["category"]
        s = category_stats[cat]

        s["apps"] += 1

        build = r.get("buildability", "unknown")
        if build in s:
            s[build] += 1

        access_value = r.get("credential_access", "unknown")

        if access_value == "partner_gated":
            s["partner_gated"] += 1

        if access_value in {
            "self_serve_free",
            "self_serve_trial",
            "paid_plan",
        }:
            s["self_serve"] += 1

        if r.get("mcp") == "found":
            s["mcp_found"] += 1

    # -----------------------------
    # First pass vs verified
    # -----------------------------

    first_pass_changes = []

    for r in results:
        changes = r.get("changed_fields", [])

        if changes:
            first_pass_changes.append({
                "app": r["app"],
                "changes": changes,
                "change_count": len(changes),
            })

    changed_field_counter = Counter()

    for item in first_pass_changes:
        for field in item["changes"]:
            changed_field_counter[field] += 1

    # -----------------------------
    # Human verification
    # -----------------------------

    human_checked = []
    pending_human = []

    for h in human:
        check = h.get("human_check", {})

        if check.get("checked") is True:
            human_checked.append(h)
        else:
            pending_human.append(h)

    human_accuracy = None
    field_accuracy = {}

    if human_checked:
        total = 0
        correct = 0

        fields = [
            "authentication",
            "credential_access",
            "api_surface",
            "api_breadth",
            "mcp",
            "buildability",
        ]

        field_totals = Counter()
        field_correct = Counter()

        for h in human_checked:
            verified = h

            # Human values are stored inside human_check
            human_values = h.get("human_check", {})

            for field in fields:
                if field in human_values and field in verified:
                    field_totals[field] += 1
                    total += 1

                    if human_values[field] == verified[field]:
                        field_correct[field] += 1
                        correct += 1

        if total:
            human_accuracy = round(correct / total * 100, 2)

        for field in field_totals:
            field_accuracy[field] = round(
                field_correct[field] / field_totals[field] * 100,
                2
            )

    # -----------------------------
    # Difficult / high-risk cases
    # -----------------------------

    difficult_cases = []

    for r in results:
        if (
            r.get("buildability") in {"blocked", "conditional"}
            or r.get("credential_access") == "partner_gated"
            or r.get("confidence") == "low"
            or r.get("mcp") == "found"
        ):
            difficult_cases.append({
                "app": r["app"],
                "category": r["category"],
                "buildability": r.get("buildability"),
                "credential_access": r.get("credential_access"),
                "mcp": r.get("mcp"),
                "confidence": r.get("confidence"),
                "blocker": r.get("blocker"),
            })

    # -----------------------------
    # Summary
    # -----------------------------

    summary = {
        "total_apps": len(results),

        "categories": counter_to_dict(categories),

        "authentication": counter_to_dict(auth),

        "credential_access": counter_to_dict(access),

        "api_surface": counter_to_dict(api_surface),

        "api_breadth": counter_to_dict(breadth),

        "mcp": counter_to_dict(mcp),

        "buildability": counter_to_dict(buildability),

        "confidence": counter_to_dict(confidence),

        "first_pass": {
            "apps_with_changes": len(first_pass_changes),
            "changed_fields": counter_to_dict(changed_field_counter),
        },

        "human_verification": {
            "sample_size": len(human),
            "checked": len(human_checked),
            "pending": len(pending_human),
            "accuracy_percent": human_accuracy,
            "field_accuracy_percent": field_accuracy,
        },

        "category_stats": dict(category_stats),

        "difficult_cases": difficult_cases,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("ANALYSIS COMPLETE")
    print(f"Apps: {len(results)}")
    print(f"Human sample: {len(human)}")
    print(f"Human checks completed: {len(human_checked)}")
    print(f"Human checks pending: {len(pending_human)}")

    if human_accuracy is not None:
        print(f"Human accuracy: {human_accuracy}%")
    else:
        print("Human accuracy: pending sufficient human confirmation")

    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()