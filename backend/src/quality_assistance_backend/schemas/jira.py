from pydantic import BaseModel


class JiraOAuthStart(BaseModel):
    authorization_url: str


class JiraConnectionStatus(BaseModel):
    configured: bool
    connected: bool
    site_name: str | None = None
    site_url: str | None = None


class JiraIssue(BaseModel):
    id: str
    key: str
    summary: str
    description: str
    issue_type: str | None = None
    status: str | None = None


class JiraIssuePage(BaseModel):
    issues: list[JiraIssue]
    next_page_token: str | None = None
