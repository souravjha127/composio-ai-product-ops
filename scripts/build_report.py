import json
import html
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

RESULTS_FILE = ROOT / "data" / "verified_results.json"
ANALYSIS_FILE = ROOT / "data" / "analysis.json"
OUTPUT_DIR = ROOT / "app"
OUTPUT_FILE = OUTPUT_DIR / "index.html"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def esc(value):
    return html.escape(str(value or ""))


def pct(value, total):
    if not total:
        return 0
    return round(value / total * 100, 1)


def badge(value):
    value = str(value or "unknown")

    cls = {
        "ready": "ready",
        "conditional": "conditional",
        "blocked": "blocked",
        "found": "found",
        "unknown": "unknown",
        "partner_gated": "gated",
        "self_serve_free": "free",
        "self_serve_trial": "trial",
        "paid_plan": "paid",
        "contact_sales": "sales",
    }.get(value, "neutral")

    label = value.replace("_", " ").replace(";", " + ")

    return f'<span class="badge {cls}">{esc(label)}</span>'


def build_stats_cards(analysis):
    total = analysis["total_apps"]

    build = analysis["buildability"]

    ready = build.get("ready", 0)
    conditional = build.get("conditional", 0)
    blocked = build.get("blocked", 0)

    return f"""
    <div class="stats-grid">

      <div class="stat-card">
        <div class="stat-number">{total}</div>
        <div class="stat-label">Apps researched</div>
      </div>

      <div class="stat-card">
        <div class="stat-number">{ready}</div>
        <div class="stat-label">Ready to build</div>
        <div class="stat-sub">{pct(ready, total)}%</div>
      </div>

      <div class="stat-card">
        <div class="stat-number">{conditional}</div>
        <div class="stat-label">Conditional</div>
        <div class="stat-sub">{pct(conditional, total)}%</div>
      </div>

      <div class="stat-card">
        <div class="stat-number">{blocked}</div>
        <div class="stat-label">Blocked</div>
        <div class="stat-sub">{pct(blocked, total)}%</div>
      </div>

      <div class="stat-card">
        <div class="stat-number">{analysis["first_pass"]["apps_with_changes"]}</div>
        <div class="stat-label">Changed after verification</div>
      </div>

    </div>
    """


def build_distribution(title, values, total):
    rows = []

    for key, count in values.items():
        rows.append(
            f"""
            <div class="dist-row">
                <div class="dist-label">{esc(key.replace("_", " "))}</div>
                <div class="dist-bar">
                    <div class="dist-fill" style="width:{pct(count,total)}%"></div>
                </div>
                <div class="dist-value">{count} ({pct(count,total)}%)</div>
            </div>
            """
        )

    return f"""
    <div class="distribution">
        <h3>{esc(title)}</h3>
        {''.join(rows)}
    </div>
    """


def build_category_table(analysis):
    rows = []

    categories = analysis["category_stats"]

    for category, stats in categories.items():
        total = stats["apps"]

        rows.append(
            f"""
            <tr>
                <td><strong>{esc(category)}</strong></td>
                <td>{total}</td>
                <td>{stats["ready"]}</td>
                <td>{stats["conditional"]}</td>
                <td>{stats["blocked"]}</td>
                <td>{stats["partner_gated"]}</td>
                <td>{stats["mcp_found"]}</td>
            </tr>
            """
        )

    return f"""
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Apps</th>
                <th>Ready</th>
                <th>Conditional</th>
                <th>Blocked</th>
                <th>Partner gated</th>
                <th>MCP found</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """


def build_app_table(results):
    rows = []

    for r in results:
        evidence = r.get("evidence", [])

        links = []

        for e in evidence[:3]:
            url = e.get("url")

            if url:
                links.append(
                    f'<a href="{esc(url)}" target="_blank" rel="noopener">source</a>'
                )

        evidence_html = " ".join(links)

        rows.append(
            f"""
            <tr>
                <td>{esc(r.get("id"))}</td>
                <td>
                    <strong>{esc(r.get("app"))}</strong>
                    <div class="small">{esc(r.get("category"))}</div>
                </td>
                <td>{badge(r.get("authentication"))}</td>
                <td>{badge(r.get("credential_access"))}</td>
                <td>{badge(r.get("api_surface"))}</td>
                <td>{badge(r.get("api_breadth"))}</td>
                <td>{badge(r.get("mcp"))}</td>
                <td>{badge(r.get("buildability"))}</td>
                <td class="evidence">{evidence_html}</td>
            </tr>
            """
        )

    return f"""
    <table id="appTable">
        <thead>
            <tr>
                <th>ID</th>
                <th>App</th>
                <th>Auth</th>
                <th>Access</th>
                <th>API</th>
                <th>Breadth</th>
                <th>MCP</th>
                <th>Buildability</th>
                <th>Evidence</th>
            </tr>
        </thead>

        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """


def main():

    results = load_json(RESULTS_FILE)
    analysis = load_json(ANALYSIS_FILE)

    OUTPUT_DIR.mkdir(exist_ok=True)

    total = analysis["total_apps"]

    auth_html = build_distribution(
        "Authentication",
        analysis["authentication"],
        total,
    )

    access_html = build_distribution(
        "Credential access",
        analysis["credential_access"],
        total,
    )

    breadth_html = build_distribution(
        "API breadth",
        analysis["api_breadth"],
        total,
    )

    build_html = build_distribution(
        "Buildability",
        analysis["buildability"],
        total,
    )

    category_html = build_category_table(analysis)

    app_html = build_app_table(results)

    changes = analysis["first_pass"]["changed_fields"]

    change_items = "".join(
        f"<li><strong>{esc(k)}</strong>: {v} changes</li>"
        for k, v in changes.items()
    )

    difficult_cases = analysis["difficult_cases"]

    difficult_rows = ""

    for r in difficult_cases[:30]:
        difficult_rows += f"""
        <tr>
            <td>{esc(r["app"])}</td>
            <td>{esc(r["category"])}</td>
            <td>{badge(r["buildability"])}</td>
            <td>{badge(r["credential_access"])}</td>
            <td>{badge(r["mcp"])}</td>
            <td>{esc(r.get("blocker") or "—")}</td>
        </tr>
        """

    human = analysis["human_verification"]

    html_doc = f"""<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>AI Product Ops — 100 App Research</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family:
        Inter,
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background: #f6f7f9;
    color: #172033;
}}

.container {{
    max-width: 1450px;
    margin: auto;
    padding: 0 28px;
}}

.hero {{
    background: #101827;
    color: white;
    padding: 70px 0 60px;
}}

.hero h1 {{
    font-size: 46px;
    line-height: 1.05;
    margin: 0 0 18px;
    letter-spacing: -1.5px;
}}

.hero p {{
    max-width: 850px;
    color: #cbd5e1;
    font-size: 18px;
    line-height: 1.65;
}}

.tag {{
    display: inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    background: #243044;
    color: #dbeafe;
    font-size: 13px;
    margin: 4px 5px 0 0;
}}

section {{
    padding: 55px 0;
}}

h2 {{
    font-size: 30px;
    margin: 0 0 12px;
}}

h3 {{
    margin-top: 0;
}}

.section-intro {{
    color: #5b6474;
    max-width: 900px;
    line-height: 1.6;
}}

.stats-grid {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(190px, 1fr));
    gap: 16px;
    margin-top: 30px;
}}

.stat-card {{
    background: white;
    border: 1px solid #e3e7ee;
    border-radius: 14px;
    padding: 22px;
    box-shadow: 0 3px 12px rgba(0,0,0,.04);
}}

.stat-number {{
    font-size: 34px;
    font-weight: 750;
}}

.stat-label {{
    margin-top: 6px;
    color: #5b6474;
}}

.stat-sub {{
    margin-top: 4px;
    color: #697386;
    font-size: 13px;
}}

.grid {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(330px, 1fr));
    gap: 20px;
}}

.distribution {{
    background: white;
    border: 1px solid #e3e7ee;
    border-radius: 14px;
    padding: 24px;
}}

.dist-row {{
    display: grid;
    grid-template-columns: 150px 1fr 90px;
    gap: 12px;
    align-items: center;
    margin: 13px 0;
    font-size: 13px;
}}

.dist-label {{
    text-transform: capitalize;
}}

.dist-bar {{
    height: 9px;
    background: #edf0f4;
    border-radius: 99px;
    overflow: hidden;
}}

.dist-fill {{
    height: 100%;
    background: #536dfe;
}}

.dist-value {{
    text-align: right;
    color: #5b6474;
}}

.card {{
    background: white;
    border: 1px solid #e3e7ee;
    border-radius: 14px;
    padding: 26px;
    margin-top: 22px;
}}

.insight-grid {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(280px, 1fr));
    gap: 18px;
    margin-top: 24px;
}}

.insight {{
    background: white;
    border: 1px solid #e3e7ee;
    border-radius: 14px;
    padding: 23px;
}}

.insight h3 {{
    margin-bottom: 9px;
}}

.insight p {{
    color: #5b6474;
    line-height: 1.55;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
    border: 1px solid #e3e7ee;
    border-radius: 12px;
    overflow: hidden;
}}

th,
td {{
    padding: 12px 13px;
    border-bottom: 1px solid #edf0f4;
    text-align: left;
    vertical-align: top;
    font-size: 13px;
}}

th {{
    background: #f8fafc;
    position: sticky;
    top: 0;
    z-index: 2;
}}

.small {{
    color: #7a8495;
    font-size: 11px;
    margin-top: 4px;
}}

.badge {{
    display: inline-block;
    padding: 5px 8px;
    border-radius: 7px;
    font-size: 11px;
    white-space: nowrap;
    background: #eef1f5;
    color: #424b5a;
}}

.badge.ready,
.badge.free,
.badge.found {{
    background: #e8f7ef;
    color: #166534;
}}

.badge.conditional,
.badge.trial,
.badge.paid {{
    background: #fff4d6;
    color: #8a5a00;
}}

.badge.blocked,
.badge.gated,
.badge.sales {{
    background: #feeceb;
    color: #a33a35;
}}

.badge.unknown {{
    background: #edf0f4;
    color: #687386;
}}

.evidence a {{
    color: #4055c7;
    text-decoration: none;
    margin-right: 5px;
}}

.evidence a:hover {{
    text-decoration: underline;
}}

.search {{
    width: 100%;
    padding: 13px 15px;
    border: 1px solid #d8dee8;
    border-radius: 10px;
    margin: 20px 0;
    font-size: 14px;
}}

.table-wrap {{
    overflow-x: auto;
}}

.workflow {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(190px, 1fr));
    gap: 12px;
    margin-top: 25px;
}}

.step {{
    background: white;
    border: 1px solid #e3e7ee;
    border-radius: 12px;
    padding: 20px;
}}

.step-number {{
    font-size: 12px;
    color: #536dfe;
    font-weight: 700;
}}

footer {{
    background: #101827;
    color: #cbd5e1;
    padding: 35px 0;
    margin-top: 20px;
}}

code {{
    background: #eef1f5;
    padding: 2px 5px;
    border-radius: 4px;
}}

@media(max-width: 700px) {{
    .hero h1 {{
        font-size: 35px;
    }}

    .container {{
        padding: 0 16px;
    }}

    .dist-row {{
        grid-template-columns: 1fr;
        gap: 5px;
    }}

    .dist-value {{
        text-align: left;
    }}
}}

</style>

</head>

<body>

<header class="hero">

<div class="container">

<div>
    <span class="tag">AI Product Ops</span>
    <span class="tag">100 Apps</span>
    <span class="tag">Evidence-first research</span>
</div>

<h1>
API & Integration Readiness
Research
</h1>

<p>
A reproducible research and verification pipeline for evaluating
100 SaaS applications across authentication, API surface,
credential accessibility, MCP availability, and buildability.
</p>

<p>
<strong>Key methodological point:</strong>
the first-pass collector is intentionally separated from the
verification layer. Unknown means “not established from the
available evidence,” not “no”.
</p>

</div>

</header>


<main>


<section>

<div class="container">

<h2>Executive findings</h2>

<p class="section-intro">
The dataset covers 100 applications across 10 categories.
The first-pass collector was followed by an evidence
re-check layer that re-fetched stored sources and corrected
ambiguous or unsupported conclusions.
</p>

{build_stats_cards(analysis)}

<div class="insight-grid">

<div class="insight">
<h3>Verification changed the dataset substantially</h3>
<p>
77 of 100 records were corrected after the first pass,
with 209 field-level changes. The largest correction areas
were credential access, API breadth, and buildability.
</p>
</div>

<div class="insight">
<h3>Access is a major build constraint</h3>
<p>
A technically available API does not automatically mean
a developer can obtain credentials. The dataset therefore
separates API existence from credential/access gating.
</p>
</div>

<div class="insight">
<h3>Unknown is treated explicitly</h3>
<p>
When official evidence could not be re-fetched or did not
support a conclusion, the pipeline retains an unknown state
rather than converting missing evidence into a negative.
</p>
</div>

<div class="insight">
<h3>MCP is tracked separately</h3>
<p>
MCP detection requires explicit MCP/model-context evidence.
Generic integrations or third-party connectors are not
automatically counted as first-party MCP support.
</p>
</div>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Research patterns</h2>

<p class="section-intro">
Distribution of the verified dataset.
Percentages use all 100 apps as the denominator.
</p>

<div class="grid">

{auth_html}

{access_html}

{breadth_html}

{build_html}

</div>

</div>

</section>


<section>

<div class="container">

<h2>Category comparison</h2>

<p class="section-intro">
A category-level view helps identify where integration
work tends to encounter access or buildability constraints.
</p>

<div class="table-wrap">

{category_html}

</div>

</div>

</section>


<section>

<div class="container">

<h2>Verification loop</h2>

<p class="section-intro">
The pipeline uses multiple stages rather than treating the
first automated extraction as ground truth.
</p>

<div class="workflow">

<div class="step">
<div class="step-number">01 — INPUT</div>
<h3>100-app dataset</h3>
<p>
Structured CSV containing category, app, website and
documentation hints.
</p>
</div>

<div class="step">
<div class="step-number">02 — FIRST PASS</div>
<h3>Evidence collector</h3>
<p>
Crawls relevant documentation pages and extracts
authentication, API, access and MCP signals.
</p>
</div>

<div class="step">
<div class="step-number">03 — VERIFICATION</div>
<h3>Evidence re-check</h3>
<p>
Re-fetches stored sources and applies stricter rules,
especially around API gating and MCP.
</p>
</div>

<div class="step">
<div class="step-number">04 — HUMAN REVIEW</div>
<h3>Stratified sample</h3>
<p>
20 records were selected to include difficult,
failed, MCP, gated and category-diverse cases.
</p>
</div>

<div class="step">
<div class="step-number">05 — REPORT</div>
<h3>Decision surface</h3>
<p>
Verified records become a searchable matrix and
category-level research findings.
</p>
</div>

</div>

</div>

</section>


<section>

<div class="container">

<h2>First-pass → verification</h2>

<div class="card">

<p>
<strong>Apps with changes:</strong>
{analysis["first_pass"]["apps_with_changes"]} / {total}
</p>

<p>
<strong>Total field-level changes:</strong>
{sum(changes.values())}
</p>

<h3>Fields most frequently corrected</h3>

<ul>
{change_items}
</ul>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Human verification status</h2>

<div class="card">

<p>
The verification sample contains
<strong>{human["sample_size"]}</strong> apps.
</p>

<p>
<strong>{human["checked"]}</strong> are currently marked as
reviewed and <strong>{human["pending"]}</strong> remain
pending confirmation.
</p>

<p>
A final independent human-accuracy percentage is intentionally
not reported until the pending records have actually been
reviewed.
</p>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Difficult cases</h2>

<p class="section-intro">
These records contain at least one higher-risk characteristic:
partner gating, blocked/conditional buildability, low confidence,
or MCP evidence.
</p>

<div class="table-wrap">

<table>

<thead>

<tr>
<th>App</th>
<th>Category</th>
<th>Buildability</th>
<th>Access</th>
<th>MCP</th>
<th>Main blocker</th>
</tr>

</thead>

<tbody>

{difficult_rows}

</tbody>

</table>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Full 100-app matrix</h2>

<p class="section-intro">
Search the complete verified dataset. Every record retains
its available evidence links.
</p>

<input
    id="search"
    class="search"
    type="text"
    placeholder="Search app, category, auth, access, API..."
>

<div class="table-wrap">

{app_html}

</div>

</div>

</section>


<section>

<div class="container">

<h2>What this research means for product ops</h2>

<div class="insight-grid">

<div class="insight">
<h3>Separate technical support from access</h3>
<p>
An API can be public while credentials remain restricted
to certain plans, partners, or enterprise customers.
These should be modeled as separate dimensions.
</p>
</div>

<div class="insight">
<h3>Prioritize evidence quality</h3>
<p>
Documentation URLs are more useful than inferred labels.
The pipeline therefore stores source URLs with each result.
</p>
</div>

<div class="insight">
<h3>Use verification where errors matter</h3>
<p>
The verifier focuses on fields that can materially change
integration decisions: access, breadth, MCP and buildability.
</p>
</div>

<div class="insight">
<h3>Keep an explicit unknown state</h3>
<p>
Missing documentation is an uncertainty signal. It should
not silently become “unsupported”.
</p>
</div>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Reproducibility</h2>

<div class="card">

<p>
This report is generated from structured JSON outputs rather
than manually edited HTML.
</p>

<p>
Core pipeline:
</p>

<ol>
<li><code>data/apps.csv</code> — 100-app input dataset</li>
<li><code>agent/researcher.py</code> — first-pass evidence collection</li>
<li><code>agent/verifier.py</code> — evidence re-check and correction</li>
<li><code>agent/analyzer.py</code> — aggregate analysis</li>
<li><code>scripts/build_report.py</code> — HTML generation</li>
</ol>

<p>
This makes the research repeatable when the input dataset
or verification rules change.
</p>

</div>

</div>

</section>


</main>


<footer>

<div class="container">

<strong>AI Product Ops — API & Integration Readiness Research</strong>

<p>
Generated from the project research pipeline.
</p>

</div>

</footer>


<script>

const searchInput = document.getElementById("search");

searchInput.addEventListener("input", function() {{

    const query = this.value.toLowerCase();

    const rows =
        document.querySelectorAll("#appTable tbody tr");

    rows.forEach(function(row) {{

        const text =
            row.innerText.toLowerCase();

        row.style.display =
            text.includes(query) ? "" : "none";

    }});

}});

</script>


</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print("REPORT BUILT")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Apps included: {len(results)}")


if __name__ == "__main__":
    main()