from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from uuid import UUID
from unittest.mock import patch

import httpx
from pydantic import SecretStr

from quality_assistance_backend.config import settings
from quality_assistance_backend.crypto.fernet_encryption import FernetEncryption
from quality_assistance_backend.schemas.jira import JiraIssue
from quality_assistance_backend.services.jira_cloud_service import (
    _issue_from_payload,
    _plain_description,
    _state_digest,
    authorization_url,
    get_issue_details,
    list_assigned_issues,
)


class JiraCloudServiceTests(unittest.TestCase):
    def test_converts_jira_adf_description_to_text(self) -> None:
        description = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "As a user, I can select a story."}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "It should display details."}],
                },
            ],
        }
        self.assertEqual(
            _plain_description(description),
            "As a user, I can select a story.\nIt should display details.",
        )

    def test_normalizes_jira_issue_fields(self) -> None:
        issue = _issue_from_payload(
            {
                "id": "1234",
                "key": "QA-42",
                "fields": {
                    "summary": "Show assigned issues",
                    "description": {
                        "type": "doc",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Display the issue title."}],
                            }
                        ],
                    },
                    "issuetype": {"name": "Story"},
                    "status": {"name": "In Progress"},
                },
            }
        )
        self.assertEqual(
            issue,
            JiraIssue(
                id="1234",
                key="QA-42",
                summary="Show assigned issues",
                description="Display the issue title.",
                issue_type="Story",
                status="In Progress",
            ),
        )

    def test_handles_missing_description(self) -> None:
        self.assertEqual(_plain_description(None), "")

    def test_oauth_url_uses_csrf_state_and_minimum_read_scopes(self) -> None:
        with (
            patch.object(settings, "jira_client_id", "client-id"),
            patch.object(settings, "jira_client_secret", SecretStr("client-secret")),
            patch.object(settings, "jira_redirect_uri", "https://app.example.com/callback"),
        ):
            parsed = urlparse(authorization_url("unpredictable-state-value"))
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.hostname, "auth.atlassian.com")
        self.assertEqual(query["state"], ["unpredictable-state-value"])
        self.assertIn("read:jira-work", query["scope"][0])
        self.assertIn("read:jira-user", query["scope"][0])
        self.assertIn("offline_access", query["scope"][0])
        self.assertNotIn("client-secret", parsed.query)

    def test_oauth_state_is_stored_as_digest(self) -> None:
        state = "random-oauth-state"
        self.assertNotEqual(_state_digest(state), state)
        self.assertEqual(len(_state_digest(state)), 64)


class JiraIssueRequestTests(unittest.IsolatedAsyncioTestCase):
    user_id = UUID("f0b4d540-0a0a-4b89-8b48-88aad7d32c2e")

    class FakeDatabase:
        def __init__(self, connection: object) -> None:
            self.connection = connection

        async def execute(self, _statement: object) -> object:
            return SimpleNamespace(scalar_one_or_none=lambda: self.connection)

    class FakeHttpClient:
        def __init__(self, response: httpx.Response) -> None:
            self.response = response
            self.request: tuple[str, dict[str, object]] | None = None

        async def __aenter__(self) -> JiraIssueRequestTests.FakeHttpClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def get(
            self,
            url: str,
            *,
            params: dict[str, object],
            headers: dict[str, str],
        ) -> httpx.Response:
            self.request = (url, params)
            return self.response

    def make_connection(self) -> SimpleNamespace:
        encryptor = FernetEncryption()
        return SimpleNamespace(
            user_id="test-user",
            cloud_id="cloud-id",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            access_token_encrypted=encryptor.encrypt("access-token"),
        )

    async def test_assigned_issue_search_uses_current_user_and_small_field_set(self) -> None:
        response = httpx.Response(
            200,
            json={
                "issues": [
                    {
                        "id": "1",
                        "key": "HD11-11326",
                        "fields": {
                            "summary": "Example user story",
                            "issuetype": {"name": "Story"},
                            "status": {"name": "Open"},
                        },
                    }
                ],
                "nextPageToken": "next-page",
            },
        )
        client = self.FakeHttpClient(response)
        database = self.FakeDatabase(self.make_connection())
        with patch(
            "quality_assistance_backend.services.jira_cloud_service.httpx.AsyncClient",
            return_value=client,
        ):
            page = await list_assigned_issues(database, user_id=self.user_id)  # type: ignore[arg-type]

        self.assertEqual(page.issues[0].key, "HD11-11326")
        self.assertEqual(page.next_page_token, "next-page")
        self.assertIsNotNone(client.request)
        _, params = client.request
        self.assertIn("assignee = currentUser()", str(params["jql"]))
        self.assertNotIn("description", str(params["fields"]))

    async def test_detail_request_rechecks_assignment(self) -> None:
        response = httpx.Response(
            200,
            json={
                "issues": [
                    {
                        "id": "1",
                        "key": "HD11-11326",
                        "fields": {
                            "summary": "Example user story",
                            "description": {
                                "type": "doc",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [{"type": "text", "text": "Story details."}],
                                    }
                                ],
                            },
                        },
                    }
                ]
            },
        )
        client = self.FakeHttpClient(response)
        database = self.FakeDatabase(self.make_connection())
        with patch(
            "quality_assistance_backend.services.jira_cloud_service.httpx.AsyncClient",
            return_value=client,
        ):
            issue = await get_issue_details(
                database,
                user_id=self.user_id,  # type: ignore[arg-type]
                issue_key="HD11-11326",
            )

        self.assertEqual(issue.description, "Story details.")
        self.assertIsNotNone(client.request)
        _, params = client.request
        self.assertIn("HD11-11326", str(params["jql"]))
        self.assertIn("assignee = currentUser()", str(params["jql"]))


if __name__ == "__main__":
    unittest.main()
