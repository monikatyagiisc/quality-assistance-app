from app.tools.stlc import summarize_requirements

REQUIREMENTS_TOOLS = [
    summarize_requirements,
]

ROOT_TOOLS = [
    *REQUIREMENTS_TOOLS,
]

__all__ = [
    "REQUIREMENTS_TOOLS",
    "ROOT_TOOLS",
    "summarize_requirements",
]
