import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "human_verification_sample.json"

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

reviews = {
    "Cloudflare": {
        "authentication": "API key; Bearer/token",
        "credential_access": "self_serve_free",
        "api_surface": "REST; SDK",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "ready",
        "evidence_urls": [
            "https://developers.cloudflare.com/api/overview/",
            "https://developers.cloudflare.com/fundamentals/api/how-to/"
        ]
    },

    "BigCommerce": {
        "authentication": "OAuth2; Bearer/token; Basic",
        "credential_access": "self_serve_free",
        "api_surface": "REST; GraphQL",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "ready",
        "evidence_urls": [
            "https://docs.bigcommerce.com/developer/docs/overview/api-fundamentals/api-accounts",
            "https://docs.bigcommerce.com/developer/docs/integrations/apps/guide/auth"
        ]
    },

    "Binance": {
        "authentication": "API key; Bearer/token",
        "credential_access": "self_serve_free",
        "api_surface": "REST",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "ready",
        "evidence_urls": [
            "https://developers.binance.com/en/docs/products/spot/rest-api",
            "https://github.com/binance/binance-spot-api-docs/blob/master/faqs/api_key_types.md"
        ]
    },

    "PitchBook": {
        "authentication": "API key; Bearer/token",
        "credential_access": "partner_gated",
        "api_surface": "REST",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "blocked",
        "evidence_urls": [
            "https://pitchbook.com/help/PitchBook-api"
        ]
    },

    "Plaid": {
        "authentication": "OAuth2; Bearer/token",
        "credential_access": "partner_gated",
        "api_surface": "REST",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "conditional",
        "evidence_urls": [
            "https://plaid.com/docs/api/oauth/",
            "https://plaid.com/docs/"
        ]
    },

    "Meta Ads": {
        "authentication": "OAuth2; Bearer/token",
        "credential_access": "partner_gated",
        "api_surface": "REST",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "conditional",
        "evidence_urls": [
            "https://developers.facebook.com/docs/marketing-api/"
        ]
    },

    "SendGrid": {
        "authentication": "API key; Bearer/token; Basic",
        "credential_access": "self_serve_free",
        "api_surface": "REST",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "ready",
        "evidence_urls": [
            "https://www.twilio.com/docs/sendgrid/for-developers/sending-email/authentication",
            "https://www.twilio.com/docs/sendgrid/api-reference/api-keys"
        ]
    },

    "Threads": {
        "authentication": "OAuth2; Bearer/token",
        "credential_access": "self_serve_free",
        "api_surface": "REST",
        "api_breadth": "moderate",
        "mcp": "unknown",
        "buildability": "ready",
        "evidence_urls": [
            "https://developers.facebook.com/docs/threads/"
        ]
    },

    "Airtable": {
        "authentication": "Bearer/token",
        "credential_access": "self_serve_free",
        "api_surface": "REST",
        "api_breadth": "moderate",
        "mcp": "unknown",
        "buildability": "ready",
        "evidence_urls": [
            "https://support.airtable.com/articles/9934989703-creating-personal-access-tokens"
        ]
    },

    "Asana": {
        "authentication": "OAuth2; Bearer/token",
        "credential_access": "self_serve_free",
        "api_surface": "REST",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "ready",
        "evidence_urls": [
            "https://developers.asana.com/docs/authentication",
            "https://developers.asana.com/docs/oauth",
            "https://developers.asana.com/docs/personal-access-token"
        ]
    },

    "Linear": {
        "authentication": "OAuth2; API key",
        "credential_access": "self_serve_free",
        "api_surface": "GraphQL; SDK",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "ready",
        "evidence_urls": [
            "https://linear.app/developers/graphql",
            "https://linear.app/developers/oauth-2-0-authentication"
        ]
    },

    "Notion": {
        "authentication": "Bearer/token",
        "credential_access": "self_serve_free",
        "api_surface": "REST",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "ready",
        "evidence_urls": [
            "https://www.notion.com/help/create-integrations-with-the-notion-api"
        ]
    },

    "Gladly": {
        "authentication": "Basic; Bearer/token",
        "credential_access": "partner_gated",
        "api_surface": "REST",
        "api_breadth": "moderate",
        "mcp": "unknown",
        "buildability": "conditional",
        "evidence_urls": [
            "https://developer.gladly.com/rest/",
            "https://help.gladly.com/docs/generate-api-tokens-and-create-webhooks"
        ]
    },

    "Plain": {
        "authentication": "Bearer/token",
        "credential_access": "self_serve_free",
        "api_surface": "GraphQL",
        "api_breadth": "moderate",
        "mcp": "unknown",
        "buildability": "ready",
        "evidence_urls": [
            "https://www.plain.com/docs/api"
        ]
    },

    "Zendesk": {
        "authentication": "OAuth2; API key; Bearer/token",
        "credential_access": "self_serve_trial",
        "api_surface": "REST",
        "api_breadth": "broad",
        "mcp": "unknown",
        "buildability": "conditional",
        "evidence_urls": [
            "https://developer.zendesk.com/documentation/authentication/",
            "https://developer.zendesk.com/documentation/authentication/api-tokens-to-oauth/",
            "https://developer.zendesk.com/api-reference/introduction/security-and-auth/"
        ]
    }
}


for record in data:
    app = record.get("app")

    if app in reviews:
        review = reviews[app]

        record["human_check"] = {
            "checked": False,
            "review_status": "pending_user_confirmation",
            **review
        }

        print(f"Added proposed review: {app}")


with open(INPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\nDONE")
print(f"Updated: {INPUT}")
print("\nIMPORTANT:")
print("These are evidence-backed proposed checks.")
print("Do not report them as independent human verification until you review/confirm them.")