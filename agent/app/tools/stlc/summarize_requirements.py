def summarize_requirements(requirements: str) -> dict:
    """Extract key themes from software requirements for test planning."""
    lines = [line.strip() for line in requirements.splitlines() if line.strip()]
    return {
        "status": "success",
        "line_count": len(lines),
        "preview": "\n".join(lines[:5]),
    }
