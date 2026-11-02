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
from quality_assistance_backend.schemas.jira import JiraCreateIssueRequest
from quality_assistance_backend.services.jira_cloud_service import (
    JiraCloudError,
    _issue_from_payload,
    _plain_description,
    _post_token,
    _state_digest,
    _jira_validation_message,
    _markdown_to_adf,
    authorization_url,
    consume_oauth_state,
    create_issue,
    get_issue_details,
    list_projects,
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
        self.assertIn("write:jira-work", query["scope"][0])
        self.assertIn("offline_access", query["scope"][0])
        self.assertNotIn("client-secret", parsed.query)

    def test_oauth_state_is_stored_as_digest(self) -> None:
        state = "random-oauth-state"
        self.assertNotEqual(_state_digest(state), state)
        self.assertEqual(len(_state_digest(state)), 64)

    def test_extracts_jira_field_validation_errors_safely(self) -> None:
        response = httpx.Response(
            400,
            json={
                "errorMessages": ["The target project is unavailable."],
                "errors": {"project": "User cannot create issues in this project."},
            },
        )

        message = _jira_validation_message(response)

        self.assertEqual(
            message,
            "The target project is unavailable.; "
            "project: User cannot create issues in this project.",
        )

    def test_converts_markdown_bug_description_to_rich_adf(self) -> None:
        adf = _markdown_to_adf(
            "- *Title*: Expired coupon `EXPIRED50`\n"
            "- *Severity*: High\n"
            "- *Steps*:\n"
            "  1. POST `/checkout/coupon`\n"
            "  2. Observe response 200.\n\n"
            "- *Expected*: 400 `CouponExpired`\n"
            "- *Actual*: 200, discount applied.\n\n"
            "See **bold text** and [Jira](https://example.com)."
        )
        content = adf["content"]

        self.assertEqual(adf["type"], "doc")
        self.assertEqual(content[0]["type"], "bulletList")
        title_item = content[0]["content"][0]["content"][0]["content"]
        self.assertEqual(title_item[0]["marks"], [{"type": "em"}])
        self.assertEqual(title_item[1]["text"], ": Expired coupon ")
        self.assertEqual(title_item[2]["marks"], [{"type": "code"}])
        self.assertEqual(content[1]["type"], "orderedList")
        step_text = content[1]["content"][0]["content"][0]["content"]
        self.assertEqual(step_text[1]["marks"], [{"type": "code"}])
        inline_content = content[3]["content"]
        self.assertEqual(inline_content[1]["marks"], [{"type": "strong"}])
        self.assertEqual(
            inline_content[3]["marks"],
            [{"type": "link", "attrs": {"href": "https://example.com"}}],
        )


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
            self.post_request: tuple[str, dict[str, object]] | None = None

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

        async def post(
            self,
            url: str,
            *,
            json: dict[str, object],
            headers: dict[str, str],
        ) -> httpx.Response:
            self.post_request = (url, json)
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

    async def test_lists_jira_projects_for_picker(self) -> None:
        response = httpx.Response(
            200,
            json={"values": [{"id": "100", "key": "QA", "name": "Quality"}]},
        )
        client = self.FakeHttpClient(response)
        database = self.FakeDatabase(self.make_connection())
        with patch(
            "quality_assistance_backend.services.jira_cloud_service.httpx.AsyncClient",
            return_value=client,
        ):
            result = await list_projects(database, user_id=self.user_id)  # type: ignore[arg-type]

        self.assertEqual(result.projects[0].key, "QA")
        self.assertIsNotNone(client.request)
        self.assertIn("/project/search", client.request[0])

    async def test_creates_jira_bug_and_returns_browse_url(self) -> None:
        response = httpx.Response(201, json={"id": "200", "key": "QA-42"})
        client = self.FakeHttpClient(response)
        connection = self.make_connection()
        connection.site_url = "https://example.atlassian.net/"
        database = self.FakeDatabase(connection)
        with patch(
            "quality_assistance_backend.services.jira_cloud_service.httpx.AsyncClient",
            return_value=client,
        ), patch(
            "quality_assistance_backend.services.jira_cloud_service.get_connection",
            return_value=connection,
        ):
            result = await create_issue(
                database,  # type: ignore[arg-type]
                user_id=self.user_id,
                issue=JiraCreateIssueRequest(
                    project_key="QA",
                    summary="Checkout total is incorrect",
                    description="- *Title*: Expired coupon `EXPIRED50`\n"
                    "1. POST `/checkout/coupon`.",
                ),
            )

        self.assertEqual(result.key, "QA-42")
        self.assertEqual(result.url, "https://example.atlassian.net/browse/QA-42")
        self.assertIsNotNone(client.post_request)
        _, payload = client.post_request
        fields = payload["fields"]
        self.assertEqual(fields["issuetype"], {"name": "Bug"})
        self.assertEqual(fields["project"], {"key": "QA"})
        description = fields["description"]
        self.assertEqual(description["type"], "doc")
        self.assertEqual(description["content"][0]["type"], "bulletList")
        self.assertEqual(description["content"][1]["type"], "orderedList")

    async def test_create_issue_unauthorized_error_explains_write_scope_reconnect(self) -> None:
        client = self.FakeHttpClient(httpx.Response(401, json={"error": "unauthorized"}))
        connection = self.make_connection()
        database = self.FakeDatabase(connection)
        with patch(
            "quality_assistance_backend.services.jira_cloud_service.httpx.AsyncClient",
            return_value=client,
        ), patch(
            "quality_assistance_backend.services.jira_cloud_service.get_connection",
            return_value=connection,
        ):
            with self.assertRaises(JiraCloudError) as raised:
                await create_issue(
                    database,  # type: ignore[arg-type]
                    user_id=self.user_id,
                    issue=JiraCreateIssueRequest(
                        project_key="QA",
                        summary="Example bug",
                        description="Example details.",
                    ),
                )

        self.assertEqual(raised.exception.status_code, 401)
        self.assertIn("write:jira-work", str(raised.exception))
        self.assertIn("Reconnect Jira", str(raised.exception))

    async def test_create_issue_includes_jira_validation_reason(self) -> None:
        client = self.FakeHttpClient(
            httpx.Response(
                400,
                json={
                    "errorMessages": [],
                    "errors": {"project": "User cannot create issues in this project."},
                },
            )
        )
        connection = self.make_connection()
        database = self.FakeDatabase(connection)
        with patch(
            "quality_assistance_backend.services.jira_cloud_service.httpx.AsyncClient",
            return_value=client,
        ), patch(
            "quality_assistance_backend.services.jira_cloud_service.get_connection",
            return_value=connection,
        ):
            with self.assertRaises(JiraCloudError) as raised:
                await create_issue(
                    database,  # type: ignore[arg-type]
                    user_id=self.user_id,
                    issue=JiraCreateIssueRequest(
                        project_key="QA",
                        summary="Example bug",
                        description="Example details.",
                    ),
                )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("project:", str(raised.exception))
        self.assertIn("cannot create issues", str(raised.exception))


class JiraOAuthTokenTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_oauth_state_has_specific_reason(self) -> None:
        class FakeDatabase:
            async def scalar(self, _statement: object) -> None:
                return None

        with self.assertRaises(JiraCloudError) as raised:
            await consume_oauth_state(FakeDatabase(), "unknown-state")  # type: ignore[arg-type]

        self.assertEqual(raised.exception.reason, "invalid_state")

    class FakeHttpClient:
        def __init__(self, response: httpx.Response) -> None:
            self.response = response

        async def __aenter__(self) -> JiraOAuthTokenTests.FakeHttpClient:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(self, *_args: object, **_kwargs: object) -> httpx.Response:
            return self.response

    async def test_invalid_client_response_has_actionable_safe_reason(self) -> None:
        client = self.FakeHttpClient(
            httpx.Response(401, json={"error": "invalid_client"})
        )
        with patch(
            "quality_assistance_backend.services.jira_cloud_service.httpx.AsyncClient",
            return_value=client,
        ):
            with self.assertRaises(JiraCloudError) as raised:
                await _post_token({"client_secret": "never-log-this"})

        self.assertEqual(raised.exception.reason, "invalid_client")
        self.assertNotIn("never-log-this", str(raised.exception))

    async def test_invalid_grant_response_identifies_callback_code_problem(self) -> None:
        client = self.FakeHttpClient(
            httpx.Response(400, json={"error": "invalid_grant"})
        )
        with patch(
            "quality_assistance_backend.services.jira_cloud_service.httpx.AsyncClient",
            return_value=client,
        ):
            with self.assertRaises(JiraCloudError) as raised:
                await _post_token({"code": "authorization-code"})

        self.assertEqual(raised.exception.reason, "invalid_grant")

    async def test_unrecognized_provider_error_uses_safe_category(self) -> None:
        client = self.FakeHttpClient(
            httpx.Response(
                400,
                json={
                    "error": "unexpected_provider_error",
                    "error_description": "sensitive provider detail",
                },
            )
        )
        with patch(
            "quality_assistance_backend.services.jira_cloud_service.httpx.AsyncClient",
            return_value=client,
        ):
            with self.assertRaises(JiraCloudError) as raised:
                await _post_token({"code": "authorization-code"})

        self.assertEqual(raised.exception.reason, "token_exchange_failed")
        self.assertNotIn("sensitive provider detail", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
