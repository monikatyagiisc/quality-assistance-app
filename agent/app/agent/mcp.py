from urllib.parse import urlsplit

from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

from app.config.settings import settings


def _build_remote_toolset(
    name: str,
    url: str | None,
    token: str | None,
) -> McpToolset | None:
    endpoint = url.strip() if url else ""
    bearer_token = token.strip() if token else ""
    if not endpoint and not bearer_token:
        return None
    if not endpoint or not bearer_token:
        raise ValueError(
            f"{name.upper()}_MCP_URL and {name.upper()}_MCP_TOKEN must be configured together"
        )

    parsed_url = urlsplit(endpoint)
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if not parsed_url.hostname or parsed_url.username or parsed_url.password:
        raise ValueError(
            f"{name.upper()}_MCP_URL must be an absolute URL without embedded credentials")
    if parsed_url.scheme != "https" and not (
        parsed_url.scheme == "http" and parsed_url.hostname in local_hosts
    ):
        raise ValueError(
            f"{name.upper()}_MCP_URL must use HTTPS (HTTP is allowed only on localhost)")

    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=endpoint,
            headers={"Authorization": f"Bearer {bearer_token}"},
        ),
        tool_name_prefix=f"{name}_",
    )


def build_mcp_toolsets() -> list[McpToolset]:
    toolsets = [
        _build_remote_toolset(
            "jira",
            settings.jira_mcp_url,
            settings.jira_mcp_token.get_secret_value() if settings.jira_mcp_token else None,
        ),
        _build_remote_toolset(
            "github",
            settings.github_mcp_url,
            settings.github_mcp_token.get_secret_value() if settings.github_mcp_token else None,
        ),
    ]
    return [toolset for toolset in toolsets if toolset is not None]
