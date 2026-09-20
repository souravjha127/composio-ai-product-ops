import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sample_path = ROOT / "data" / "human_verification_sample.json"

with open(sample_path, encoding="utf-8") as f:
    sample = json.load(f)


HUMAN_CHECKS = {
    "Otter AI": {
        "authentication": "Bearer/token",
        "credential_access": "partner_gated",
        "api_surface": "REST",
        "api_breadth": "moderate",
        "mcp": "unknown",
        "buildability": "blocked",
        "notes": (
            "Official public API documentation describes Bearer-token "
            "authentication and availability for Enterprise workspaces."
        ),
        "evidence_urls": [
            "https://help.otter.ai/hc/en-us/articles/36130822688279-Otter-ai-Public-API"
        ],
    },

    "Pipedrive": {
        "authentication": "OAuth2; API key",
        "credential_access": "self_serve_free",
        "api_surface": "REST",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "ready",
        "notes": (
            "Official API reference documents a RESTful API, API token "
            "authentication, OAuth 2.0 and broad coverage of core product "
            "resources."
        ),
        "evidence_urls": [
            "https://developers.pipedrive.com/docs/api/v1",
            "https://developers.pipedrive.com/docs/api/v1/Oauth",
        ],
    },

    "Salesforce": {
        "authentication": "OAuth2; Bearer/token",
        "credential_access": "self_serve_free",
        "api_surface": "REST",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "ready",
        "notes": (
            "Official Salesforce REST API documentation confirms OAuth 2.0 "
            "authorization and bearer access tokens. Developer Edition is "
            "available for testing and development."
        ),
        "evidence_urls": [
            "https://developer.salesforce.com/docs/platform/api-rest/guide/intro-oauth-and-connected-apps.html",
            "https://developer.salesforce.com/docs/platform/api-rest/guide/quickstart.html",
            "https://developer.salesforce.com/docs/platform/api-rest/guide/intro-rest-compatible-editions.html",
        ],
    },

    "Pumble": {
        "authentication": "API key",
        "credential_access": "self_serve_free",
        "api_surface": "REST",
        "api_breadth": "moderate",
        "mcp": "unknown",
        "buildability": "conditional",
        "notes": (
            "Pumble documents API-key generation and API access. "
            "The API requires the relevant API addon/workspace setup."
        ),
        "evidence_urls": [
            "https://pumble.com/help/integrations/automation-workflow-integrations/api-keys-integration/",
        ],
    },

    "MrScraper": {
        "authentication": "API key",
        "credential_access": "self_serve_free",
        "api_surface": "REST",
        "api_breadth": "broad",
        "mcp": "found",
        "buildability": "ready",
        "notes": (
            "Official documentation provides a REST API with API-token "
            "authentication and documents an MCP server."
        ),
        "evidence_urls": [
            "https://docs.mrscraper.com/docs/api/overview",
            "https://docs.mrscraper.com/docs/getting-started/mcp-server",
        ],
    },
}


updated = 0

for record in sample:
    app = record["app"]

    if app not in HUMAN_CHECKS:
        continue

    check = HUMAN_CHECKS[app]

    record["human_check"] = {
        "checked": True,
        "authentication": check["authentication"],
        "credential_access": check["credential_access"],
        "api_surface": check["api_surface"],
        "api_breadth": check["api_breadth"],
        "mcp": check["mcp"],
        "buildability": check["buildability"],
        "notes": check["notes"],
        "evidence_urls": check["evidence_urls"],
    }

    updated += 1


with open(sample_path, "w", encoding="utf-8") as f:
    json.dump(sample, f, indent=2, ensure_ascii=False)


print("=" * 60)
print("HUMAN VERIFICATION UPDATED")
print("=" * 60)
print(f"Apps updated: {updated}")
print(f"File: {sample_path}")
print()

for record in sample:
    hc = record.get("human_check", {})

    if hc.get("checked"):
        print(
            f"{record['sample_id']:02d}. "
            f"{record['app']} -> HUMAN CHECKED"
        )

print()
print("Next: inspect the JSON and then verify the remaining 15 apps.")