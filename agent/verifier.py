import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = BASE_DIR / "data" / "raw_research.json"
OUTPUT_FILE = BASE_DIR / "data" / "verified_results.json"
SAMPLE_FILE = BASE_DIR / "data" / "verification_sample.json"

REQUEST_TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
    )
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ============================================================
# VERIFICATION PATTERNS
# ============================================================

# Stronger authentication evidence.
AUTH_RULES = {
    "OAuth2": [
        r"\boauth 2\.0\b",
        r"\boauth2\b",
        r"\boauth\b.*\bapi\b",
        r"\bapi\b.*\boauth\b",
        r"\bauthorization code\b",
        r"\baccess token\b.*\brefresh token\b",
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
        r"\bauthorization: bearer\b",
        r"\bbearer authentication\b",
        r"\bpersonal access token\b",
        r"\bapi token\b",
    ],
}


# Strong API evidence.
API_RULES = {
    "REST": [
        r"\brest api\b",
        r"\brestful api\b",
        r"\brest endpoints?\b",
        r"\bhttp api\b",
        r"\bapi reference\b",
    ],

    "GraphQL": [
        r"\bgraphql api\b",
        r"\bgraphql endpoint\b",
        r"\bgraphql\b.*\bapi\b",
        r"\bapi\b.*\bgraphql\b",
    ],

    "SOAP": [
        r"\bsoap api\b",
        r"\bsoap web service\b",
        r"\bsoap endpoint\b",
    ],

    "SDK": [
        r"\bsdk\b",
        r"\bsoftware development kit\b",
        r"\bpython sdk\b",
        r"\bjavascript sdk\b",
        r"\bnode sdk\b",
    ],
}


# IMPORTANT:
# MCP verification is intentionally much stricter than the
# researcher. Generic occurrences of "MCP" are not enough.
MCP_STRONG_PATTERNS = [
    r"\bmodel context protocol\b",
    r"\bmcp server\b",
    r"\bmcp endpoint\b",
    r"\bmcp connector\b",
    r"\bmcp integration\b",
    r"\bremote mcp\b",
    r"\bmodel-context-protocol\b",
]


# Terms indicating that the MCP reference is probably about
# an actual integration rather than generic marketing text.
MCP_ACTION_PATTERNS = [
    r"\bconnect\b",
    r"\binstall\b",
    r"\bconfigure\b",
    r"\bserver\b",
    r"\bendpoint\b",
    r"\bclient\b",
    r"\btool\b",
    r"\btransport\b",
    r"\bstdio\b",
    r"\bsse\b",
    r"\bstreamable http\b",
]


# Access restrictions need to be tied to API/developer access.
ACCESS_RULES = {
    "partner_gated": [
        r"\bapi\b.{0,120}\bpartner\b",
        r"\bpartner\b.{0,120}\bapi\b",
        r"\bdeveloper\b.{0,120}\bpartner\b",
        r"\bpartner\b.{0,120}\bdeveloper\b",
        r"\bpartner[- ]only\b.{0,120}\bapi\b",
    ],

    "contact_sales": [
        r"\bapi\b.{0,150}\bcontact sales\b",
        r"\bapi\b.{0,150}\btalk to sales\b",
        r"\bapi\b.{0,150}\bspeak to sales\b",
        r"\bdeveloper access\b.{0,150}\bsales\b",
        r"\bapi access\b.{0,150}\bsales\b",
    ],

    "paid_plan": [
        r"\bapi\b.{0,150}\bpaid plan\b",
        r"\bapi\b.{0,150}\bprofessional plan\b",
        r"\bapi\b.{0,150}\benterprise plan\b",
        r"\bapi access\b.{0,150}\bsubscription\b",
        r"\bapi access\b.{0,150}\bplan\b",
    ],

    "self_serve_trial": [
        r"\bapi\b.{0,150}\bfree trial\b",
        r"\bdeveloper\b.{0,150}\bfree trial\b",
        r"\bapi access\b.{0,150}\btrial\b",
    ],

    "self_serve_free": [
        r"\bapi\b.{0,150}\bfree\b",
        r"\bdeveloper\b.{0,150}\bfree\b",
        r"\bfree\b.{0,150}\bapi\b",
        r"\bfree developer account\b",
    ],
}


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_text(text):
    return clean_text(text).lower()


def fetch_page(url):
    try:
        response = SESSION.get(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        content_type = response.headers.get(
            "Content-Type",
            "",
        )

        if response.status_code >= 400:
            return {
                "url": url,
                "final_url": response.url,
                "status": response.status_code,
                "ok": False,
                "title": "",
                "text": "",
                "error": f"HTTP {response.status_code}",
            }

        if "html" not in content_type.lower():
            return {
                "url": url,
                "final_url": response.url,
                "status": response.status_code,
                "ok": True,
                "title": "",
                "text": "",
                "error": "Non-HTML content",
            }

        soup = BeautifulSoup(response.text, "lxml")

        for tag in soup([
            "script",
            "style",
            "noscript",
            "svg",
        ]):
            tag.decompose()

        title = ""

        if soup.title:
            title = clean_text(
                soup.title.get_text(" ")
            )

        text = clean_text(
            soup.get_text(" ")
        )

        return {
            "url": url,
            "final_url": response.url,
            "status": response.status_code,
            "ok": True,
            "title": title,
            "text": text,
            "error": "",
        }

    except requests.RequestException as exc:
        return {
            "url": url,
            "final_url": url,
            "status": None,
            "ok": False,
            "title": "",
            "text": "",
            "error": str(exc),
        }


def extract_snippets(text, patterns, window=220):
    """
    Return evidence around actual pattern matches.
    """

    if not text:
        return []

    snippets = []

    for pattern in patterns:
        try:
            for match in re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                start = max(
                    0,
                    match.start() - window,
                )

                end = min(
                    len(text),
                    match.end() + window,
                )

                snippet = clean_text(
                    text[start:end]
                )

                if (
                    snippet
                    and snippet not in snippets
                ):
                    snippets.append(snippet)

                if len(snippets) >= 3:
                    return snippets

        except re.error:
            continue

    return snippets


def all_evidence_pages(result):
    """
    Pull URLs stored by the researcher.

    The researcher already collected source_pages.
    We re-fetch those pages rather than trusting old snippets.
    """

    urls = []

    for source in result.get(
        "source_pages",
        [],
    ):
        url = source.get("url")

        if url and url not in urls:
            urls.append(url)

    # Also include URLs stored directly in evidence.
    for item in result.get(
        "evidence",
        [],
    ):
        url = item.get("url")

        if url and url not in urls:
            urls.append(url)

    return urls


# ============================================================
# AUTHENTICATION VERIFICATION
# ============================================================

def verify_authentication(pages):
    found = []
    evidence = []

    combined_pages = []

    for page in pages:
        if page.get("ok") and page.get("text"):
            combined_pages.append(page)

    for auth_type, patterns in AUTH_RULES.items():

        for page in combined_pages:

            snippets = extract_snippets(
                page["text"],
                patterns,
            )

            if not snippets:
                continue

            found.append(auth_type)

            evidence.append({
                "claim": "authentication",
                "value": auth_type,
                "url": page["final_url"],
                "title": page["title"],
                "snippets": snippets,
            })

    # Deduplicate.
    found = list(dict.fromkeys(found))

    if not found:
        return "unknown", evidence

    return "; ".join(found), evidence


# ============================================================
# API SURFACE VERIFICATION
# ============================================================

def verify_api_surface(pages):
    found = []
    evidence = []

    for api_type, patterns in API_RULES.items():

        for page in pages:

            snippets = extract_snippets(
                page["text"],
                patterns,
            )

            if not snippets:
                continue

            found.append(api_type)

            evidence.append({
                "claim": "api_surface",
                "value": api_type,
                "url": page["final_url"],
                "title": page["title"],
                "snippets": snippets,
            })

    found = list(dict.fromkeys(found))

    if not found:
        return "unknown", evidence

    return "; ".join(found), evidence


# ============================================================
# MCP VERIFICATION
# ============================================================

def verify_mcp(pages):
    """
    Strict MCP verification.

    We require:
    1. Explicit Model Context Protocol OR strong MCP terminology.
    2. Context suggesting an actual MCP integration/server/endpoint.

    Merely finding "MCP" in a page is not enough.
    """

    evidence = []

    for page in pages:

        text = page.get("text", "")

        strong_snippets = extract_snippets(
            text,
            MCP_STRONG_PATTERNS,
            window=280,
        )

        if not strong_snippets:
            continue

        valid_snippets = []

        for snippet in strong_snippets:

            snippet_lower = snippet.lower()

            action_found = any(
                re.search(
                    pattern,
                    snippet_lower,
                    flags=re.IGNORECASE,
                )
                for pattern in MCP_ACTION_PATTERNS
            )

            if action_found:
                valid_snippets.append(
                    snippet
                )

        if valid_snippets:

            evidence.append({
                "claim": "mcp",
                "value": "found",
                "url": page["final_url"],
                "title": page["title"],
                "snippets": valid_snippets,
                "verification_rule": (
                    "Explicit MCP terminology plus "
                    "implementation/integration context."
                ),
            })

    if evidence:
        return "found", evidence

    return "unknown", []


# ============================================================
# ACCESS VERIFICATION
# ============================================================

def verify_access(pages):
    """
    Verify API/developer credential access.

    Generic pricing/contact-sales language is NOT enough.
    """

    evidence = []

    priority = [
        "partner_gated",
        "contact_sales",
        "paid_plan",
        "self_serve_trial",
        "self_serve_free",
    ]

    for access_type in priority:

        patterns = ACCESS_RULES[
            access_type
        ]

        for page in pages:

            snippets = extract_snippets(
                page["text"],
                patterns,
                window=260,
            )

            if not snippets:
                continue

            evidence.append({
                "claim": "credential_access",
                "value": access_type,
                "url": page["final_url"],
                "title": page["title"],
                "snippets": snippets,
            })

    # Strongest explicit restriction wins.
    values = [
        item["value"]
        for item in evidence
    ]

    if not values:
        return "unknown", []

    values = list(dict.fromkeys(values))

    for value in priority:
        if value in values:
            matching = [
                item
                for item in evidence
                if item["value"] == value
            ]

            return value, matching

    return "unknown", []


# ============================================================
# BREADTH VERIFICATION
# ============================================================

def verify_breadth(pages, api_surface):
    """
    Estimate API breadth from explicit documentation concepts.

    This is still a heuristic, not an endpoint count.
    """

    if api_surface == "unknown":
        return "unknown", []

    concepts = {
        "authentication": [
            r"\bauthentication\b",
            r"\bauth\b",
        ],
        "endpoints": [
            r"\bendpoints?\b",
        ],
        "resources": [
            r"\bresources?\b",
        ],
        "webhooks": [
            r"\bwebhooks?\b",
        ],
        "pagination": [
            r"\bpagination\b",
            r"\bpaginate\b",
        ],
        "rate limits": [
            r"\brate limits?\b",
            r"\brate limiting\b",
        ],
        "API reference": [
            r"\bapi reference\b",
            r"\breference documentation\b",
        ],
        "SDK": [
            r"\bsdk\b",
        ],
        "versioning": [
            r"\bapi version\b",
            r"\bversioning\b",
        ],
        "search": [
            r"\bsearch endpoint\b",
            r"\bsearch api\b",
        ],
        "bulk": [
            r"\bbulk api\b",
            r"\bbulk operations?\b",
        ],
    }

    combined = " ".join(
        page["text"]
        for page in pages
        if page.get("ok") and page.get("text")
    )

    detected = []

    for concept, patterns in concepts.items():

        for pattern in patterns:

            if re.search(
                pattern,
                combined,
                flags=re.IGNORECASE,
            ):
                detected.append(concept)
                break

    count = len(detected)

    if count >= 8:
        return "broad", detected

    if count >= 4:
        return "moderate", detected

    if count >= 1:
        return "narrow", detected

    return "unknown", detected


# ============================================================
# BUILDABILITY
# ============================================================

def calculate_buildability(
    authentication,
    access,
    api_surface,
    mcp,
):
    if access == "partner_gated":
        return "blocked"

    if (
        api_surface != "unknown"
        and authentication != "unknown"
        and access in {
            "self_serve_free",
            "self_serve_trial",
        }
    ):
        return "ready"

    if (
        api_surface != "unknown"
        and authentication != "unknown"
        and access == "paid_plan"
    ):
        return "conditional"

    if mcp == "found":
        return "conditional"

    if access == "contact_sales":
        return "conditional"

    if api_surface != "unknown":
        return "conditional"

    return "unknown"


def calculate_blocker(
    authentication,
    access,
    api_surface,
    mcp,
):
    if access == "partner_gated":
        return "partner approval/access"

    if access == "contact_sales":
        return "API/developer access requires sales"

    if api_surface == "unknown":
        return "API surface not sufficiently verified"

    if authentication == "unknown":
        return "authentication method not sufficiently verified"

    if access == "unknown":
        return "API credential/access requirements unclear"

    if mcp == "found":
        return "no major blocker identified from public evidence"

    return "none identified"


# ============================================================
# COMPARE FIRST PASS VS VERIFIED
# ============================================================

def compare_value(
    original,
    verified,
):
    if original == verified:
        return {
            "changed": False,
            "original": original,
            "verified": verified,
        }

    return {
        "changed": True,
        "original": original,
        "verified": verified,
    }


# ============================================================
# VERIFY ONE APP
# ============================================================

def verify_app(result):
    print(
        f"  Verifying evidence: {result['app']}"
    )

    urls = all_evidence_pages(result)

    pages = []

    for url in urls:

        page = fetch_page(url)

        pages.append(page)

        time.sleep(0.15)

    usable_pages = [
        page
        for page in pages
        if page.get("ok")
        and page.get("text")
    ]

    # --------------------------------------------------------
    # Verify individual claims
    # --------------------------------------------------------

    authentication, auth_evidence = (
        verify_authentication(
            usable_pages
        )
    )

    api_surface, api_evidence = (
        verify_api_surface(
            usable_pages
        )
    )

    access, access_evidence = (
        verify_access(
            usable_pages
        )
    )

    mcp, mcp_evidence = (
        verify_mcp(
            usable_pages
        )
    )

    breadth, breadth_concepts = (
        verify_breadth(
            usable_pages,
            api_surface,
        )
    )

    buildability = calculate_buildability(
        authentication,
        access,
        api_surface,
        mcp,
    )

    blocker = calculate_blocker(
        authentication,
        access,
        api_surface,
        mcp,
    )

    # --------------------------------------------------------
    # Changes
    # --------------------------------------------------------

    changes = {
        "authentication": compare_value(
            result.get(
                "authentication",
                "unknown",
            ),
            authentication,
        ),

        "credential_access": compare_value(
            result.get(
                "credential_access",
                "unknown",
            ),
            access,
        ),

        "api_surface": compare_value(
            result.get(
                "api_surface",
                "unknown",
            ),
            api_surface,
        ),

        "api_breadth": compare_value(
            result.get(
                "api_breadth",
                "unknown",
            ),
            breadth,
        ),

        "mcp": compare_value(
            result.get(
                "mcp",
                "unknown",
            ),
            mcp,
        ),

        "buildability": compare_value(
            result.get(
                "buildability",
                "unknown",
            ),
            buildability,
        ),
    }

    changed_fields = [
        field
        for field, item in changes.items()
        if item["changed"]
    ]

    # --------------------------------------------------------
    # Evidence quality
    # --------------------------------------------------------

    evidence_count = (
        len(auth_evidence)
        + len(api_evidence)
        + len(access_evidence)
        + len(mcp_evidence)
    )

    if evidence_count >= 6:
        verification_confidence = "high"
    elif evidence_count >= 3:
        verification_confidence = "medium"
    elif evidence_count >= 1:
        verification_confidence = "low"
    else:
        verification_confidence = "very_low"

    if not usable_pages:
        verification_status = "failed"

    elif changed_fields:
        verification_status = "corrected"

    else:
        verification_status = "confirmed"

    # --------------------------------------------------------
    # Issues
    # --------------------------------------------------------

    issues = []

    if result.get("mcp") == "found" and mcp == "unknown":
        issues.append(
            "MCP was reported by the first-pass researcher "
            "but could not be confirmed with strong evidence."
        )

    if (
        result.get("credential_access")
        in {
            "partner_gated",
            "contact_sales",
        }
        and access == "unknown"
    ):
        issues.append(
            "First-pass access restriction was not "
            "sufficiently tied to API/developer access."
        )

    if (
        result.get("authentication") != "unknown"
        and authentication == "unknown"
    ):
        issues.append(
            "First-pass authentication claim could not "
            "be confirmed."
        )

    if (
        result.get("api_surface") != "unknown"
        and api_surface == "unknown"
    ):
        issues.append(
            "First-pass API-surface claim could not "
            "be confirmed."
        )

    if not usable_pages:
        issues.append(
            "Evidence pages could not be re-fetched."
        )

    # --------------------------------------------------------
    # Verified result
    # --------------------------------------------------------

    verified = dict(result)

    verified.update({
        "authentication": authentication,
        "credential_access": access,
        "api_surface": api_surface,
        "api_breadth": breadth,
        "mcp": mcp,
        "buildability": buildability,
        "main_blocker": blocker,

        "verified_evidence": (
            auth_evidence
            + api_evidence
            + access_evidence
            + mcp_evidence
        ),

        "verified_breadth_concepts": (
            breadth_concepts
        ),

        "verification_status": (
            verification_status
        ),

        "verification_confidence": (
            verification_confidence
        ),

        "changed_fields": changed_fields,
        "verification_changes": changes,
        "verification_issues": issues,

        "verification_method": (
            "Automated re-fetch of stored evidence URLs "
            "followed by conservative rule-based validation. "
            "Claims are corrected when strong evidence does "
            "not support the first-pass value."
        ),
    })

    return verified


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    original_results,
    verified_results,
):
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

    total = len(verified_results)

    changed_apps = 0
    changed_fields = 0
    confirmed_apps = 0
    failed_apps = 0

    for result in verified_results:

        if result.get(
            "verification_status"
        ) == "corrected":
            changed_apps += 1

        elif result.get(
            "verification_status"
        ) == "confirmed":
            confirmed_apps += 1

        elif result.get(
            "verification_status"
        ) == "failed":
            failed_apps += 1

        changed_fields += len(
            result.get(
                "changed_fields",
                [],
            )
        )

    print(f"Apps verified: {total}")
    print(f"Confirmed: {confirmed_apps}")
    print(f"Corrected: {changed_apps}")
    print(f"Failed: {failed_apps}")
    print(f"Changed fields: {changed_fields}")

    # --------------------------------------------------------
    # Field-level changes
    # --------------------------------------------------------

    print("\nField changes:")

    fields = [
        "authentication",
        "credential_access",
        "api_surface",
        "api_breadth",
        "mcp",
        "buildability",
    ]

    for field in fields:

        count = 0

        for result in verified_results:
            change = result.get(
                "verification_changes",
                {},
            ).get(field, {})

            if change.get("changed"):
                count += 1

        print(
            f"  {field}: {count}"
        )

    # --------------------------------------------------------
    # Verified distributions
    # --------------------------------------------------------

    print("\nVerified authentication:")

    counts = {}

    for result in verified_results:
        value = result.get(
            "authentication",
            "unknown",
        )

        counts[value] = (
            counts.get(value, 0) + 1
        )

    for value, count in sorted(
        counts.items(),
        key=lambda x: (-x[1], x[0]),
    ):
        print(
            f"  {value}: {count}"
        )

    print("\nVerified credential access:")

    counts = {}

    for result in verified_results:
        value = result.get(
            "credential_access",
            "unknown",
        )

        counts[value] = (
            counts.get(value, 0) + 1
        )

    for value, count in sorted(
        counts.items(),
        key=lambda x: (-x[1], x[0]),
    ):
        print(
            f"  {value}: {count}"
        )

    print("\nVerified MCP:")

    counts = {}

    for result in verified_results:
        value = result.get(
            "mcp",
            "unknown",
        )

        counts[value] = (
            counts.get(value, 0) + 1
        )

    for value, count in sorted(
        counts.items(),
        key=lambda x: (-x[1], x[0]),
    ):
        print(
            f"  {value}: {count}"
        )

    print("\nVerified buildability:")

    counts = {}

    for result in verified_results:
        value = result.get(
            "buildability",
            "unknown",
        )

        counts[value] = (
            counts.get(value, 0) + 1
        )

    for value, count in sorted(
        counts.items(),
        key=lambda x: (-x[1], x[0]),
    ):
        print(
            f"  {value}: {count}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("AI PRODUCT OPS VERIFICATION AGENT")
    print("Evidence re-check + correction")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input: {INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as f:
        original_results = json.load(f)

    if not original_results:
        raise ValueError(
            "raw_research.json contains no results."
        )

    verified_results = []

    for index, result in enumerate(
        original_results,
        start=1,
    ):

        print(
            f"\n[{index}/{len(original_results)}]"
        )

        try:
            verified = verify_app(result)

            verified_results.append(
                verified
            )

        except Exception as exc:

            print(
                f"  VERIFICATION ERROR: "
                f"{type(exc).__name__}: {exc}"
            )

            failed = dict(result)

            failed.update({
                "verification_status": "failed",
                "verification_confidence": "very_low",
                "changed_fields": [],
                "verification_changes": {},
                "verification_issues": [
                    f"Verifier error: {exc}"
                ],
                "verification_method": (
                    "Automated verifier encountered an error."
                ),
            })

            verified_results.append(
                failed
            )

    # --------------------------------------------------------
    # Save verified results
    # --------------------------------------------------------

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
            verified_results,
            f,
            indent=2,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # Save a verification sample
    #
    # For now this is simply all pilot results.
    # Later, with 100 apps, we'll make this a stratified sample.
    # --------------------------------------------------------

    sample = []

    for result in verified_results:

        sample.append({
            "id": result.get("id"),
            "app": result.get("app"),
            "category": result.get("category"),

            "first_pass": {
                "authentication": result.get(
                    "verification_changes",
                ).get(
                    "authentication",
                    {},
                ).get(
                    "original",
                    result.get(
                        "authentication"
                    ),
                ),

                "credential_access": result.get(
                    "verification_changes",
                ).get(
                    "credential_access",
                    {},
                ).get(
                    "original",
                    result.get(
                        "credential_access"
                    ),
                ),

                "api_surface": result.get(
                    "verification_changes",
                ).get(
                    "api_surface",
                    {},
                ).get(
                    "original",
                    result.get(
                        "api_surface"
                    ),
                ),

                "api_breadth": result.get(
                    "verification_changes",
                ).get(
                    "api_breadth",
                    {},
                ).get(
                    "original",
                    result.get(
                        "api_breadth"
                    ),
                ),

                "mcp": result.get(
                    "verification_changes",
                ).get(
                    "mcp",
                    {},
                ).get(
                    "original",
                    result.get("mcp"),
                ),
            },

            "verified": {
                "authentication": result.get(
                    "authentication"
                ),
                "credential_access": result.get(
                    "credential_access"
                ),
                "api_surface": result.get(
                    "api_surface"
                ),
                "api_breadth": result.get(
                    "api_breadth"
                ),
                "mcp": result.get(
                    "mcp"
                ),
                "buildability": result.get(
                    "buildability"
                ),
            },

            "status": result.get(
                "verification_status"
            ),

            "changed_fields": result.get(
                "changed_fields",
                [],
            ),

            "issues": result.get(
                "verification_issues",
                [],
            ),

            "evidence": result.get(
                "verified_evidence",
                [],
            ),
        })

    with open(
        SAMPLE_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            sample,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print_summary(
        original_results,
        verified_results,
    )

    print("\nOutput:")
    print(
        f"  {OUTPUT_FILE}"
    )

    print("\nVerification sample:")
    print(
        f"  {SAMPLE_FILE}"
    )


if __name__ == "__main__":
    main()