import json
import html
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

RESULTS = ROOT / "data" / "verified_results.json"
ANALYSIS = ROOT / "data" / "analysis.json"
OUT = ROOT / "app" / "index.html"


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def e(value):
    return html.escape(str(value or ""))


def label(value):
    return str(value or "unknown").replace("_", " ").replace(";", " + ")


def badge(value):
    value = str(value or "unknown")
    cls = value.replace("_", "-").replace(";", "-")
    return f'<span class="badge {e(cls)}">{e(label(value))}</span>'


def percent(value, total):
    return round(value / total * 100, 1) if total else 0


def distribution(title, data, total):
    rows = []

    for key, value in data.items():
        rows.append(f"""
        <div class="dist">
            <div class="dist-name">{e(label(key))}</div>
            <div class="bar">
                <div class="bar-fill" style="width:{percent(value,total)}%"></div>
            </div>
            <div class="dist-count">{value} · {percent(value,total)}%</div>
        </div>
        """)

    return f"""
    <div class="panel">
        <h3>{e(title)}</h3>
        {''.join(rows)}
    </div>
    """


def app_rows(results):
    rows = []

    for r in results:
        evidence = r.get("verified_evidence") or r.get("evidence") or []

        links = []

        for item in evidence[:3]:
            url = item.get("url")

            if url:
                links.append(
                    f'<a href="{e(url)}" target="_blank" rel="noopener">Source</a>'
                )

        changes = r.get("changed_fields", [])
        status = r.get("verification_status", "unknown")

        rows.append(f"""
        <tr>
            <td>{e(r.get("id"))}</td>

            <td>
                <strong>{e(r.get("app"))}</strong>
                <div class="muted">{e(r.get("category"))}</div>
            </td>

            <td class="description">
                {e(r.get("description"))}
            </td>

            <td>{badge(r.get("authentication"))}</td>

            <td>{badge(r.get("credential_access"))}</td>

            <td>{badge(r.get("api_surface"))}</td>

            <td>{badge(r.get("api_breadth"))}</td>

            <td>{badge(r.get("mcp"))}</td>

            <td>{badge(r.get("buildability"))}</td>

            <td>
                {e(r.get("main_blocker") or "—")}
            </td>

            <td>
                {badge(status)}
                <div class="muted">
                    {len(changes)} field changes
                </div>
            </td>

            <td class="sources">
                {" ".join(links) if links else "No source"}
            </td>
        </tr>
        """)

    return "".join(rows)


def category_rows(analysis):
    rows = []

    for category, s in analysis["category_stats"].items():
        rows.append(f"""
        <tr>
            <td><strong>{e(category)}</strong></td>
            <td>{s["apps"]}</td>
            <td>{s["ready"]}</td>
            <td>{s["conditional"]}</td>
            <td>{s["blocked"]}</td>
            <td>{s["unknown"]}</td>
            <td>{s["partner_gated"]}</td>
            <td>{s["mcp_found"]}</td>
        </tr>
        """)

    return "".join(rows)


def difficult_rows(analysis):
    rows = []

    for r in analysis["difficult_cases"]:
        rows.append(f"""
        <tr>
            <td><strong>{e(r["app"])}</strong></td>
            <td>{e(r["category"])}</td>
            <td>{badge(r.get("buildability"))}</td>
            <td>{badge(r.get("credential_access"))}</td>
            <td>{badge(r.get("mcp"))}</td>
            <td>{e(r.get("blocker") or "—")}</td>
        </tr>
        """)

    return "".join(rows)


def main():

    results = load(RESULTS)
    analysis = load(ANALYSIS)

    total = len(results)

    build = analysis["buildability"]

    ready = build.get("ready", 0)
    conditional = build.get("conditional", 0)
    blocked = build.get("blocked", 0)
    unknown = build.get("unknown", 0)

    changed = analysis["first_pass"]["apps_with_changes"]
    changed_fields = sum(
        analysis["first_pass"]["changed_fields"].values()
    )

    human = analysis["human_verification"]

    html_doc = f"""<!doctype html>
<html lang="en">

<head>

<meta charset="utf-8">

<meta name="viewport"
      content="width=device-width,initial-scale=1">

<title>AI Product Ops — 100 App Research</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family:
        Inter,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background: #f5f7fb;
    color: #172033;
}}

.hero {{
    background: #101828;
    color: white;
    padding: 65px 0;
}}

.container {{
    width: min(1500px, calc(100% - 40px));
    margin: auto;
}}

.hero h1 {{
    font-size: clamp(36px, 5vw, 62px);
    line-height: 1;
    letter-spacing: -2px;
    margin: 18px 0;
}}

.hero p {{
    max-width: 900px;
    color: #cbd5e1;
    font-size: 18px;
    line-height: 1.65;
}}

.pill {{
    display: inline-block;
    background: #263348;
    color: #dbeafe;
    padding: 7px 12px;
    border-radius: 99px;
    margin-right: 6px;
    font-size: 13px;
}}

section {{
    padding: 55px 0;
}}

h2 {{
    font-size: 32px;
    margin-bottom: 10px;
}}

h3 {{
    margin-top: 0;
}}

.lead {{
    color: #5f6b7a;
    line-height: 1.65;
    max-width: 900px;
}}

.stats {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit,minmax(170px,1fr));
    gap: 16px;
    margin-top: 28px;
}}

.stat {{
    background: white;
    border: 1px solid #e2e7ef;
    border-radius: 14px;
    padding: 22px;
}}

.stat-number {{
    font-size: 34px;
    font-weight: 800;
}}

.stat-label {{
    color: #687386;
    margin-top: 5px;
}}

.grid {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit,minmax(330px,1fr));
    gap: 20px;
}}

.panel {{
    background: white;
    border: 1px solid #e2e7ef;
    border-radius: 14px;
    padding: 24px;
}}

.dist {{
    display: grid;
    grid-template-columns: 150px 1fr 100px;
    gap: 12px;
    align-items: center;
    margin: 14px 0;
    font-size: 13px;
}}

.bar {{
    height: 9px;
    background: #edf1f6;
    border-radius: 99px;
    overflow: hidden;
}}

.bar-fill {{
    height: 100%;
    background: #536dfe;
}}

.dist-count {{
    text-align: right;
    color: #667085;
}}

.insights {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit,minmax(250px,1fr));
    gap: 18px;
    margin-top: 25px;
}}

.insight {{
    background: white;
    border: 1px solid #e2e7ef;
    border-radius: 14px;
    padding: 23px;
}}

.insight p {{
    color: #5f6b7a;
    line-height: 1.55;
}}

.workflow {{
    display: grid;
    grid-template-columns:
        repeat(auto-fit,minmax(180px,1fr));
    gap: 12px;
}}

.step {{
    background: white;
    border: 1px solid #e2e7ef;
    border-radius: 12px;
    padding: 20px;
}}

.step-num {{
    color: #536dfe;
    font-size: 12px;
    font-weight: 800;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
}}

th,
td {{
    border-bottom: 1px solid #e9edf3;
    padding: 12px;
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

.table-wrap {{
    overflow: auto;
    border: 1px solid #e2e7ef;
    border-radius: 14px;
}}

.description {{
    min-width: 260px;
    max-width: 360px;
    line-height: 1.45;
}}

.muted {{
    color: #7a8495;
    font-size: 11px;
    margin-top: 4px;
}}

.badge {{
    display: inline-block;
    background: #edf1f5;
    color: #46505e;
    padding: 5px 8px;
    border-radius: 7px;
    font-size: 11px;
    white-space: nowrap;
}}

.badge.ready,
.badge.found,
.badge.self-serve-free {{
    background: #e8f7ef;
    color: #166534;
}}

.badge.conditional,
.badge.self-serve-trial,
.badge.paid-plan {{
    background: #fff4d6;
    color: #8a5a00;
}}

.badge.blocked,
.badge.partner-gated,
.badge.contact-sales {{
    background: #feeceb;
    color: #a33a35;
}}

.sources {{
    white-space: nowrap;
}}

.sources a {{
    color: #4055c7;
    text-decoration: none;
}}

.search {{
    width: 100%;
    padding: 14px;
    border: 1px solid #d7dde7;
    border-radius: 10px;
    margin: 18px 0;
    font-size: 14px;
}}

.notice {{
    background: #fff8e7;
    border: 1px solid #f0d88a;
    border-radius: 12px;
    padding: 18px;
    line-height: 1.6;
}}

footer {{
    background: #101828;
    color: #cbd5e1;
    padding: 35px 0;
}}

code {{
    background: #edf1f5;
    padding: 2px 5px;
    border-radius: 4px;
}}

@media(max-width:700px) {{
    .container {{
        width: min(100% - 24px,1500px);
    }}

    .dist {{
        grid-template-columns: 1fr;
    }}

    .dist-count {{
        text-align: left;
    }}
}}

</style>

</head>

<body>


<header class="hero">

<div class="container">

<div>
<span class="pill">AI Product Ops</span>
<span class="pill">100 Apps</span>
<span class="pill">Evidence-first</span>
<span class="pill">Verification loop</span>
</div>

<h1>
API & Integration<br>
Readiness Research
</h1>

<p>
A reproducible research pipeline evaluating 100 SaaS
applications across authentication, credential accessibility,
API surface, API breadth, MCP availability and buildability.
</p>

<p>
The first-pass collector is intentionally separated from the
verification layer. An <strong>unknown</strong> result means
the evidence did not establish the answer; it is not treated
as a negative.
</p>

</div>

</header>


<main>


<section>

<div class="container">

<h2>Executive findings</h2>

<p class="lead">
The dataset covers 100 applications across 10 categories.
The evidence-first collector was followed by a second-pass
verification layer that re-fetched sources and revised
unsupported or ambiguous conclusions where the available
evidence allowed.
</p>

<div class="stats">

<div class="stat">
<div class="stat-number">{total}</div>
<div class="stat-label">Apps researched</div>
</div>

<div class="stat">
<div class="stat-number">{ready}</div>
<div class="stat-label">Ready</div>
</div>

<div class="stat">
<div class="stat-number">{conditional}</div>
<div class="stat-label">Conditional</div>
</div>

<div class="stat">
<div class="stat-number">{blocked}</div>
<div class="stat-label">Blocked</div>
</div>

<div class="stat">
<div class="stat-number">{unknown}</div>
<div class="stat-label">Unknown</div>
</div>

<div class="stat">
<div class="stat-number">{changed}</div>
<div class="stat-label">Records with changes</div>
</div>

<div class="stat">
<div class="stat-number">{changed_fields}</div>
<div class="stat-label">Field-level changes</div>
</div>

</div>

<div class="insights">

<div class="insight">
<h3>Access ≠ API existence</h3>
<p>
An API can exist while credentials or developer access
remain restricted. The dataset models these dimensions
separately.
</p>
</div>

<div class="insight">
<h3>Verification mattered</h3>
<p>
The second pass produced field-level changes in {changed}
of {total} records, with {changed_fields} field-level changes
recorded.
</p>
</div>

<div class="insight">
<h3>Unknown is explicit</h3>
<p>
Failed or insufficient evidence is retained as unknown
instead of being converted into “not supported”.
</p>
</div>

<div class="insight">
<h3>MCP is conservative</h3>
<p>
Generic integrations are not automatically counted as MCP.
The detector looks for explicit MCP/model-context evidence.
</p>
</div>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Research patterns</h2>

<div class="grid">

{distribution("Authentication", analysis["authentication"], total)}

{distribution("Credential access", analysis["credential_access"], total)}

{distribution("API surface", analysis["api_surface"], total)}

{distribution("API breadth", analysis["api_breadth"], total)}

{distribution("MCP", analysis["mcp"], total)}

{distribution("Buildability", analysis["buildability"], total)}

</div>

</div>

</section>


<section>

<div class="container">

<h2>Agent workflow</h2>

<p class="lead">
The implementation separates collection, verification,
analysis and presentation so that individual stages can
be rerun without manually rebuilding the entire report.
</p>

<div class="workflow">

<div class="step">
<div class="step-num">01 · INPUT</div>
<h3>100-app dataset</h3>
<p>CSV with category, website and documentation hints.</p>
</div>

<div class="step">
<div class="step-num">02 · RESEARCH</div>
<h3>Evidence collector</h3>
<p>Crawls relevant pages and extracts structured signals.</p>
</div>

<div class="step">
<div class="step-num">03 · VERIFY</div>
<h3>Verification agent</h3>
<p>Re-fetches sources and applies stricter rules.</p>
</div>

<div class="step">
<div class="step-num">04 · HUMAN</div>
<h3>Stratified sample</h3>
<p>20 records selected across categories and difficult cases.</p>
</div>

<div class="step">
<div class="step-num">05 · ANALYZE</div>
<h3>Pattern analysis</h3>
<p>Aggregates auth, access, API, MCP and buildability.</p>
</div>

<div class="step">
<div class="step-num">06 · REPORT</div>
<h3>HTML output</h3>
<p>Generates this searchable single-page research surface.</p>
</div>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Verification methodology</h2>

<div class="panel">

<ol>

<li>
The first pass stores source URLs and extracted evidence.
</li>

<li>
The verifier re-fetches the stored evidence rather than
blindly trusting first-pass classifications.
</li>

<li>
API access is only considered gated when the evidence relates
to API/developer access, rather than a generic pricing page.
</li>

<li>
MCP is counted conservatively and generic third-party
integrations are not treated as first-party MCP support.
</li>

<li>
Buildability is derived from the verified API, authentication,
access and MCP signals.
</li>

<li>
Records whose evidence cannot be established remain
<strong>unknown</strong>.
</li>

</ol>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Category comparison</h2>

<div class="table-wrap">

<table>

<thead>
<tr>
<th>Category</th>
<th>Apps</th>
<th>Ready</th>
<th>Conditional</th>
<th>Blocked</th>
<th>Unknown</th>
<th>Partner gated</th>
<th>MCP found</th>
</tr>
</thead>

<tbody>

{category_rows(analysis)}

</tbody>

</table>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Human verification status</h2>

<div class="notice">

<strong>
{human["checked"]} / {human["sample_size"]}
records are currently marked as checked.
</strong>

<br><br>

{human["pending"]} records remain pending user confirmation.

<br><br>

No final independent human-accuracy percentage is reported
while the sample is incomplete.

</div>

</div>

</section>


<section>

<div class="container">

<h2>Difficult / high-risk cases</h2>

<p class="lead">
These records contain at least one characteristic that can
materially affect integration planning: partner gating,
conditional/blocked buildability, low confidence or MCP evidence.
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

{difficult_rows(analysis)}

</tbody>

</table>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Full 100-app research matrix</h2>

<p class="lead">
Search across app names, descriptions, authentication,
access, API surface and buildability.
</p>

<input
    id="search"
    class="search"
    placeholder="Search the 100-app matrix..."
>

<div class="table-wrap">

<table id="matrix">

<thead>

<tr>
<th>ID</th>
<th>App / Category</th>
<th>Description</th>
<th>Authentication</th>
<th>Credential access</th>
<th>API surface</th>
<th>API breadth</th>
<th>MCP</th>
<th>Buildability</th>
<th>Main blocker</th>
<th>Verification</th>
<th>Evidence</th>
</tr>

</thead>

<tbody>

{app_rows(results)}

</tbody>

</table>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Reproducibility</h2>

<div class="panel">

<p>
The report is generated from structured project artifacts,
not manually edited HTML.
</p>

<ol>
<li><code>data/apps.csv</code> — research input</li>
<li><code>agent/researcher.py</code> — first-pass collection</li>
<li><code>agent/verifier.py</code> — evidence re-check</li>
<li><code>agent/analyzer.py</code> — analysis</li>
<li><code>scripts/build_final_report.py</code> — report generation</li>
</ol>

<p>
This separation allows the research to be rerun when the
dataset or verification rules change.
</p>

</div>

</div>

</section>


<section>

<div class="container">

<h2>Relationship to Composio</h2>

<div class="panel">

<p>
The research dimensions were chosen around practical agent
integration concerns: authentication, available tools/APIs,
credential access, buildability and MCP.
</p>

<p>
Composio's documentation describes toolkits as collections of
app tools together with authentication requirements, while
sessions scope users, tool access and authentication. Its MCP
session flow can expose a configured session through an MCP
endpoint.
</p>

<p>
This project does <strong>not</strong> claim that the research
collector itself used Composio. Instead, the output is designed
to demonstrate the product-ops workflow that such an integration
layer needs to support.
</p>

</div>

</div>

</section>


</main>


<footer>

<div class="container">

<strong>
AI Product Ops — API & Integration Readiness Research
</strong>

<p>
Generated from the reproducible research pipeline.
</p>

</div>

</footer>


<script>

const search = document.getElementById("search");

search.addEventListener("input", function() {{

    const query = this.value.toLowerCase();

    document
        .querySelectorAll("#matrix tbody tr")
        .forEach(row => {{

            row.style.display =
                row.innerText
                .toLowerCase()
                .includes(query)
                ? ""
                : "none";

        }});

}});

</script>


</body>
</html>
"""

    OUT.parent.mkdir(exist_ok=True)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print("FINAL REPORT BUILT")
    print(f"Output: {OUT}")
    print(f"Apps: {total}")


if __name__ == "__main__":
    main()