from pydantic import BaseModel, Field, field_validator


class RepositoryConnectionInput(BaseModel):
    provider: str = Field(default="github", max_length=32)
    owner: str = Field(min_length=1, max_length=255)
    repo: str = Field(min_length=1, max_length=255)
    default_branch: str = Field(default="main", min_length=1, max_length=128)
    access_token: str | None = Field(
        default=None,
        description="Personal access token (PAT). Leave empty to keep an existing token.",
    )

    @field_validator("owner", "repo", "default_branch")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value cannot be empty")
        return cleaned

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        provider = value.strip().lower()
        if provider not in {"github"}:
            raise ValueError("Only github is supported today")
        return provider


class RepositoryConnectionPublic(BaseModel):
    provider: str
    owner: str
    repo: str
    default_branch: str
    has_token: bool
    repo_label: str

    model_config = {"from_attributes": True}


class FetchDiffInput(BaseModel):
    base: str | None = Field(
        default=None,
        description="Base ref (branch, tag, or SHA). Defaults to the configured default branch.",
    )
    head: str | None = Field(
        default=None,
        description="Head ref to compare against base. Required unless pull_number is set.",
    )
    pull_number: int | None = Field(
        default=None,
        ge=1,
        description="GitHub pull request number. When set, base/head are ignored.",
    )


class FetchDiffOutput(BaseModel):
    diff: str
    source: str
    summary: str
