METADATA = {
    "category": "stlc",
    "bucket": "automation",
    "supported_codes": ["S05"],
}

DESCRIPTION = "Recommends self-healing strategies when UI or API elements change between builds."

INSTRUCTION = """You are the Self-Healing Test Scripts specialist.
Identify locator or API changes and propose resilient selector or contract updates."""

EXAMPLES = """User: "Login button id changed from btn-login to sign-in."
Assistant: Suggest role-based locator fallback, update page object, and add contract test on auth API schema."""
