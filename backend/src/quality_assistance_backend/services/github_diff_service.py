from __future__ import annotations

import httpx
from fastapi import HTTPException, status


class GitHubDiffService:
    """Fetch unified diffs from GitHub using a user PAT (server-side only)."""

    def __init__(self, *, owner: str, repo: str, token: str | None = None) -> None:
        self.owner = owner
        self.repo = repo
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    async def fetch_pull_diff(self, pull_number: int) -> tuple[str, str]:
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls/{pull_number}"
        headers = {**self._headers, "Accept": "application/vnd.github.v3.diff"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pull request not found. Check the PR number and repository settings.",
            )
        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub rejected the access token. Update it in Settings.",
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not fetch the pull request diff from GitHub.",
            )

        summary = f"PR #{pull_number} ({self.owner}/{self.repo})"
        return response.text, summary

    async def fetch_compare_diff(self, base: str, head: str) -> tuple[str, str]:
        url = (
            f"https://api.github.com/repos/{self.owner}/{self.repo}/compare/"
            f"{base}...{head}"
        )
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=self._headers)

        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compare refs not found. Check branch names and repository settings.",
            )
        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub rejected the access token. Update it in Settings.",
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not compare branches on GitHub.",
            )

        payload = response.json()
        files = payload.get("files") or []
        chunks: list[str] = []
        for file_info in files:
            patch = file_info.get("patch")
            if not patch:
                continue
            filename = file_info.get("filename", "unknown")
            chunks.append(
                f"diff --git a/{filename} b/{filename}\n"
                f"--- a/{filename}\n"
                f"+++ b/{filename}\n"
                f"{patch}"
            )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No file changes found between the selected refs.",
            )

        summary = f"{base}...{head} ({self.owner}/{self.repo}, {len(chunks)} file(s))"
        return "\n\n".join(chunks), summary
