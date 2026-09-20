import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = BASE_DIR / "data" / "apps.csv"
OUTPUT_FILE = BASE_DIR / "data" / "raw_research.json"

# Keep this at 5 for the next pilot.
# Change to None after we approve the pilot.
PILOT_LIMIT = None

REQUEST_TIMEOUT = 15
MAX_PAGES_PER_APP = 10
MAX_LINKS_FROM_PAGE = 25

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ============================================================
# KEYWORDS
# ============================================================

AUTH_PATTERNS = {
    "OAuth2": [
        r"\boauth 2\.0\b",
        r"\boauth2\b",
        r"\boauth\b",
        r"\bopenid connect\b",
    ],
    "API key": [
        r"\bapi key\b",
        r"\bapi-key\b",
        r"\bx-api-key\b",
        r"\bapikey\b",
    ],
    "Basic": [
        r"\bbasic authentication\b",
        r"\bbasic auth\b",
        r"\bhttp basic\b",
    ],
    "Bearer/token": [
        r"\bbearer token\b",
        r"\bbearer authentication\b",
        r"\baccess token\b",
        r"\bauthentication token\b",
        r"\bapi token\b",
        r"\bpersonal access token\b",
    ],
}

API_PATTERNS = {
    "REST": [
        r"\brest api\b",
        r"\brestful api\b",
        r"\bhttp api\b",
        r"\bjson api\b",
        r"\bendpoint\b",
    ],
    "GraphQL": [
        r"\bgraphql\b",
        r"\bgraphql api\b",
    ],
    "SOAP": [
        r"\bsoap api\b",
        r"\bsoap web service\b",
    ],
    "SDK": [
        r"\bsdk\b",
        r"\bsoftware development kit\b",
    ],
}

MCP_PATTERNS = [
    r"\bmodel context protocol\b",
    r"\bmcp server\b",
    r"\bmcp endpoint\b",
    r"\bmcp integration\b",
    r"\bmcp connector\b",
    r"\bremote mcp\b",
]

ACCESS_PATTERNS = {
    "partner_gated": [
        r"\bpartner access\b",
        r"\bpartner program\b",
        r"\bapproved partners\b",
        r"\bpartner-only\b",
        r"\bpartner only\b",
    ],
    "contact_sales": [
        r"\bcontact sales\b",
        r"\btalk to sales\b",
        r"\bspeak to sales\b",
        r"\bcontact our sales team\b",
    ],
    "paid_plan": [
        r"\bpaid plan\b",
        r"\bprofessional plan\b",
        r"\benterprise plan\b",
        r"\bavailable on.*plan\b",
        r"\brequires.*subscription\b",
    ],
    "self_serve_trial": [
        r"\bfree trial\b",
        r"\bstart.*trial\b",
        r"\btrial available\b",
        r"\bsign up.*free\b",
    ],
    "self_serve_free": [
        r"\bfree developer account\b",
        r"\bfree account\b",
        r"\bavailable for free\b",
        r"\bfree api\b",
        r"\bno cost\b",
    ],
}

PAGE_KEYWORDS = [
    "api",
    "developer",
    "developers",
    "docs",
    "documentation",
    "reference",
    "authentication",
    "auth",
    "oauth",
    "token",
    "credential",
    "integration",
    "integrations",
    "webhook",
    "mcp",
    "graphql",
    "rest",
    "sdk",
]


# ============================================================
# HELPERS
# ============================================================

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_url(url):
    if not url:
        return ""

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url.rstrip("/")


def same_domain(url1, url2):
    try:
        d1 = urlparse(url1).netloc.lower().replace("www.", "")
        d2 = urlparse(url2).netloc.lower().replace("www.", "")
        return d1 == d2
    except Exception:
        return False


def get_page(url):
    try:
        response = SESSION.get(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        final_url = response.url

        if response.status_code >= 400:
            return {
                "url": url,
                "final_url": final_url,
                "status": response.status_code,
                "ok": False,
                "title": "",
                "description": "",
                "text": "",
                "links": [],
                "error": f"HTTP {response.status_code}",
            }

        content_type = response.headers.get("Content-Type", "")

        if "text/html" not in content_type.lower():
            return {
                "url": url,
                "final_url": final_url,
                "status": response.status_code,
                "ok": True,
                "title": "",
                "description": "",
                "text": "",
                "links": [],
                "error": "Non-HTML response",
            }

        soup = BeautifulSoup(response.text, "lxml")

        # Remove noisy elements.
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()

        title = ""
        if soup.title:
            title = clean_text(soup.title.get_text(" "))

        description = ""

        meta_description = soup.find(
            "meta",
            attrs={"name": re.compile("^description$", re.I)}
        )

        if meta_description:
            description = clean_text(
                meta_description.get("content", "")
            )

        text = clean_text(soup.get_text(" "))

        links = []

        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()

            if not href:
                continue

            absolute = urljoin(final_url, href)

            if not absolute.startswith(("http://", "https://")):
                continue

            anchor_text = clean_text(a.get_text(" "))

            links.append({
                "url": absolute,
                "text": anchor_text,
            })

        return {
            "url": url,
            "final_url": final_url,
            "status": response.status_code,
            "ok": True,
            "title": title,
            "description": description,
            "text": text,
            "links": links,
            "error": "",
        }

    except requests.RequestException as exc:
        return {
            "url": url,
            "final_url": url,
            "status": None,
            "ok": False,
            "title": "",
            "description": "",
            "text": "",
            "links": [],
            "error": str(exc),
        }


def keyword_score(url, anchor_text):
    value = f"{url} {anchor_text}".lower()

    score = 0

    for keyword in PAGE_KEYWORDS:
        if keyword in value:
            score += 1

    return score


def select_links(page):
    candidates = []

    for link in page.get("links", []):
        url = link["url"]
        text = link["text"]

        if not same_domain(page["final_url"], url):
            continue

        score = keyword_score(url, text)

        if score <= 0:
            continue

        candidates.append(
            (
                score,
                len(url),
                url,
                text,
            )
        )

    # Highest keyword score first.
    candidates.sort(
        key=lambda x: (-x[0], x[1])
    )

    results = []

    seen = set()

    for _, _, url, text in candidates:
        clean_url = url.split("#")[0]

        if clean_url in seen:
            continue

        seen.add(clean_url)

        results.append({
            "url": clean_url,
            "text": text,
        })

        if len(results) >= MAX_LINKS_FROM_PAGE:
            break

    return results


def find_context(text, patterns, window=180):
    """
    Return short evidence snippets around matching terms.
    """
    snippets = []

    if not text:
        return snippets

    lowered = text.lower()

    for pattern in patterns:
        try:
            match = re.search(pattern, lowered)

            if not match:
                continue

            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)

            snippet = clean_text(text[start:end])

            if snippet and snippet not in snippets:
                snippets.append(snippet)

        except re.error:
            continue

    return snippets[:3]


def detect_auth(pages):
    scores = {
        "OAuth2": 0,
        "API key": 0,
        "Basic": 0,
        "Bearer/token": 0,
    }

    evidence = []

    for page in pages:
        text = page.get("text", "")

        for auth_type, patterns in AUTH_PATTERNS.items():
            snippets = find_context(text, patterns)

            if snippets:
                scores[auth_type] += len(snippets)

                evidence.append({
                    "claim": "authentication",
                    "value": auth_type,
                    "url": page["final_url"],
                    "title": page["title"],
                    "snippets": snippets,
                })

    found = [
        auth
        for auth, score in scores.items()
        if score > 0
    ]

    if not found:
        return "unknown", evidence

    # If multiple methods exist, report all.
    # This is more accurate than forcing one.
    if len(found) == 1:
        return found[0], evidence

    return "; ".join(found), evidence


def detect_api_surface(pages):
    scores = {
        "REST": 0,
        "GraphQL": 0,
        "SOAP": 0,
        "SDK": 0,
    }

    evidence = []

    for page in pages:
        text = page.get("text", "")

        for api_type, patterns in API_PATTERNS.items():
            snippets = find_context(text, patterns)

            if snippets:
                scores[api_type] += len(snippets)

                evidence.append({
                    "claim": "api_surface",
                    "value": api_type,
                    "url": page["final_url"],
                    "title": page["title"],
                    "snippets": snippets,
                })

    found = [
        api_type
        for api_type, score in scores.items()
        if score > 0
    ]

    if not found:
        return "unknown", evidence

    return "; ".join(found), evidence


def detect_mcp(pages):
    evidence = []

    for page in pages:
        text = page.get("text", "")

        snippets = find_context(
            text,
            MCP_PATTERNS,
            window=220,
        )

        if snippets:
            evidence.append({
                "claim": "mcp",
                "value": "found",
                "url": page["final_url"],
                "title": page["title"],
                "snippets": snippets,
            })

    if evidence:
        return "found", evidence

    return "unknown", evidence


def detect_access(pages):
    scores = {
        "partner_gated": 0,
        "contact_sales": 0,
        "paid_plan": 0,
        "self_serve_trial": 0,
        "self_serve_free": 0,
    }

    evidence = []

    for page in pages:
        text = page.get("text", "")

        for access_type, patterns in ACCESS_PATTERNS.items():
            snippets = find_context(
                text,
                patterns,
                window=200,
            )

            if snippets:
                scores[access_type] += len(snippets)

                evidence.append({
                    "claim": "credential_access",
                    "value": access_type,
                    "url": page["final_url"],
                    "title": page["title"],
                    "snippets": snippets,
                })

    found = [
        access
        for access, score in scores.items()
        if score > 0
    ]

    if not found:
        return "unknown", evidence

    # Important:
    # Contact-sales on a general pricing page does NOT automatically
    # mean API access is gated.
    #
    # We therefore downgrade generic contact-sales evidence unless
    # the snippet also contains API/developer/credential language.

    filtered = []

    for item in evidence:
        if item["value"] != "contact_sales":
            filtered.append(item)
            continue

        joined = " ".join(item["snippets"]).lower()

        if any(
            word in joined
            for word in [
                "api",
                "developer",
                "developer access",
                "credentials",
                "authentication",
                "integration",
            ]
        ):
            filtered.append(item)

    meaningful_values = {
        item["value"]
        for item in filtered
    }

    if not meaningful_values:
        return "unknown", []

    # Prefer explicit gating over generic availability.
    priority = [
        "partner_gated",
        "contact_sales",
        "paid_plan",
        "self_serve_trial",
        "self_serve_free",
    ]

    for item in priority:
        if item in meaningful_values:
            return item, filtered

    return "unknown", filtered


def estimate_api_breadth(pages):
    """
    Heuristic:
    Count distinct API concepts found in the collected evidence.
    This is NOT a claim about exact endpoint count.
    """

    concepts = {
        "authentication",
        "endpoint",
        "resource",
        "webhook",
        "pagination",
        "rate limit",
        "schema",
        "reference",
        "sdk",
        "version",
        "search",
        "bulk",
    }

    combined = " ".join(
        page.get("text", "").lower()
        for page in pages
    )

    found = [
        concept
        for concept in concepts
        if concept in combined
    ]

    count = len(found)

    if count >= 8:
        breadth = "broad"
    elif count >= 4:
        breadth = "moderate"
    elif count >= 1:
        breadth = "narrow"
    else:
        breadth = "unknown"

    return breadth, found


def buildability_verdict(
    auth,
    access,
    api_surface,
    mcp,
):
    if access == "partner_gated":
        return "blocked"

    if access == "contact_sales":
        return "conditional"

    if api_surface == "unknown" and mcp == "unknown":
        return "unknown"

    if api_surface != "unknown" and auth != "unknown":
        if access in {
            "self_serve_free",
            "self_serve_trial",
            "paid_plan",
            "unknown",
        }:
            return "ready"

    if mcp == "found":
        return "conditional"

    return "conditional"


def main_blocker(
    auth,
    access,
    api_surface,
    mcp,
):
    if access == "partner_gated":
        return "partner approval/access"

    if access == "contact_sales":
        return "sales-gated access"

    if api_surface == "unknown":
        return "API surface unclear"

    if auth == "unknown":
        return "authentication method unclear"

    if access == "unknown":
        return "credential/access requirements unclear"

    if mcp == "found":
        return "none identified from first-party evidence"

    return "none identified"


def extract_description(pages, app_name, category):
    """
    Prefer official metadata over a generated description.
    """

    for page in pages:
        description = page.get("description", "")

        if description and len(description) >= 30:
            return description[:300]

    # Fall back to title if metadata is absent.
    for page in pages:
        title = page.get("title", "")

        if title:
            return f"{app_name} — {clean_text(title)[:220]}"

    return f"{app_name} is a {category} product."


def confidence_score(
    pages,
    auth,
    api_surface,
    access,
    mcp,
):
    score = 0

    usable_pages = [
        p for p in pages
        if p.get("ok") and p.get("text")
    ]

    if usable_pages:
        score += 20

    if len(usable_pages) >= 3:
        score += 15

    if auth != "unknown":
        score += 20

    if api_surface != "unknown":
        score += 20

    if access != "unknown":
        score += 15

    if mcp != "unknown":
        score += 10

    if score >= 75:
        return "high", score

    if score >= 45:
        return "medium", score

    return "low", score


def research_app(row):
    app_id = int(row["id"])
    app_name = str(row["app"])
    category = str(row["category"])
    website = normalize_url(str(row["website"]))
    docs_hint = normalize_url(str(row["docs_hint"]))

    # --------------------------------------------------------
    # Seed URLs
    # --------------------------------------------------------

    seed_urls = []

    for url in [
        docs_hint,
        website,
    ]:
        if url and url not in seed_urls:
            seed_urls.append(url)

    pages = []
    visited = set()
    queue = list(seed_urls)

    while queue and len(pages) < MAX_PAGES_PER_APP:
        url = queue.pop(0)

        if url in visited:
            continue

        visited.add(url)

        page = get_page(url)
        pages.append(page)

        if not page.get("ok"):
            continue

        # Find relevant same-domain documentation links.
        candidates = select_links(page)

        for candidate in candidates:
            next_url = candidate["url"]

            if next_url in visited:
                continue

            if next_url not in queue:
                queue.append(next_url)

        # Don't hammer websites.
        time.sleep(0.25)

    usable_pages = [
        page
        for page in pages
        if page.get("ok") and page.get("text")
    ]

    auth, auth_evidence = detect_auth(usable_pages)

    api_surface, api_evidence = detect_api_surface(
        usable_pages
    )

    access, access_evidence = detect_access(
        usable_pages
    )

    mcp, mcp_evidence = detect_mcp(
        usable_pages
    )

    breadth, breadth_concepts = estimate_api_breadth(
        usable_pages
    )

    description = extract_description(
        usable_pages,
        app_name,
        category,
    )

    verdict = buildability_verdict(
        auth,
        access,
        api_surface,
        mcp,
    )

    blocker = main_blocker(
        auth,
        access,
        api_surface,
        mcp,
    )

    confidence, confidence_score_value = confidence_score(
        usable_pages,
        auth,
        api_surface,
        access,
        mcp,
    )

    # --------------------------------------------------------
    # Evidence records
    # --------------------------------------------------------

    evidence = []

    for item in auth_evidence:
        evidence.append(item)

    for item in api_evidence:
        evidence.append(item)

    for item in access_evidence:
        evidence.append(item)

    for item in mcp_evidence:
        evidence.append(item)

    # Deduplicate evidence.
    unique_evidence = []
    evidence_seen = set()

    for item in evidence:
        key = (
            item["claim"],
            item["value"],
            item["url"],
        )

        if key in evidence_seen:
            continue

        evidence_seen.add(key)
        unique_evidence.append(item)

    source_pages = []

    for page in pages:
        source_pages.append({
            "url": page.get("final_url", page.get("url")),
            "status": page.get("status"),
            "ok": page.get("ok"),
            "title": page.get("title", ""),
            "description": page.get("description", ""),
            "error": page.get("error", ""),
        })

    return {
        "id": app_id,
        "category": category,
        "app": app_name,
        "website": website,
        "docs_hint": docs_hint,

        "description": description,

        "authentication": auth,
        "credential_access": access,
        "api_surface": api_surface,
        "api_breadth": breadth,
        "mcp": mcp,

        "buildability": verdict,
        "main_blocker": blocker,

        "confidence": confidence,
        "confidence_score": confidence_score_value,

        "breadth_concepts_detected": breadth_concepts,

        "evidence": unique_evidence,
        "source_pages": source_pages,

        "method": (
            "First-pass automated collection from official "
            "website/docs pages using requests + BeautifulSoup. "
            "Claims are evidence-backed where possible; "
            "absence of evidence is reported as unknown."
        ),

        "verification_status": "not_verified",
    }


# ============================================================
# SUMMARY
# ============================================================

def print_counts(results):
    print("\n" + "=" * 60)
    print("RESEARCH COMPLETE")
    print("=" * 60)

    print(f"Apps researched: {len(results)}")
    print(f"Output: {OUTPUT_FILE}")

    fields = [
        ("Authentication", "authentication"),
        ("Credential access", "credential_access"),
        ("API surface", "api_surface"),
        ("API breadth", "api_breadth"),
        ("MCP", "mcp"),
        ("Buildability", "buildability"),
        ("Confidence", "confidence"),
    ]

    for label, key in fields:
        counts = {}

        for result in results:
            value = result.get(key, "unknown")
            counts[value] = counts.get(value, 0) + 1

        print(f"\n{label}:")

        for value, count in sorted(
            counts.items(),
            key=lambda x: (-x[1], x[0])
        ):
            print(f"  {value}: {count}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("AI PRODUCT OPS RESEARCH AGENT")
    print("Evidence-first first-pass collector")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing dataset: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "id",
        "category",
        "app",
        "website",
        "docs_hint",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns in apps.csv: {missing}"
        )

    if PILOT_LIMIT is not None:
        working_df = df.head(PILOT_LIMIT)
    else:
        working_df = df

    results = []

    for _, row in working_df.iterrows():
        print(
            f"Researching {row['id']}: {row['app']}"
        )

        try:
            result = research_app(row)
            results.append(result)

        except Exception as exc:
            print(
                f"  ERROR: {type(exc).__name__}: {exc}"
            )

            results.append({
                "id": int(row["id"]),
                "category": str(row["category"]),
                "app": str(row["app"]),
                "website": normalize_url(
                    str(row["website"])
                ),
                "docs_hint": normalize_url(
                    str(row["docs_hint"])
                ),

                "description": "",
                "authentication": "unknown",
                "credential_access": "unknown",
                "api_surface": "unknown",
                "api_breadth": "unknown",
                "mcp": "unknown",
                "buildability": "unknown",
                "main_blocker": "research error",
                "confidence": "low",
                "confidence_score": 0,

                "breadth_concepts_detected": [],
                "evidence": [],
                "source_pages": [],

                "method": "research error",
                "verification_status": "not_verified",

                "error": str(exc),
            })

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print_counts(results)


if __name__ == "__main__":
    main()