from pydantic import BaseModel, Field


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


class JiraProject(BaseModel):
    id: str
    key: str
    name: str


class JiraProjectList(BaseModel):
    projects: list[JiraProject]


class JiraCreateIssueRequest(BaseModel):
    project_key: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]*$", max_length=64)
    summary: str = Field(min_length=1, max_length=255)
    description: str = Field(max_length=20000)


class JiraCreatedIssue(BaseModel):
    id: str
    key: str
    summary: str
    url: str
