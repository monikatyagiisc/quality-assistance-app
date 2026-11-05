from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import HTTPException

from quality_assistance_backend.services.github_diff_service import GitHubDiffService


class GitHubDiffServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_lists_pull_requests_with_authenticated_request(self) -> None:
        response = httpx.Response(
            200,
            json=[
                {
                    "number": 42,
                    "title": "Add coupon validation",
                    "state": "open",
                    "head": {"ref": "feature/coupon-validation"},
                    "base": {"ref": "main"},
                }
            ],
        )
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.get.return_value = response
        service = GitHubDiffService(owner="example", repo="shop", token="test-token")

        with patch(
            "quality_assistance_backend.services.github_diff_service.httpx.AsyncClient",
            return_value=client,
        ):
            pull_requests = await service.list_pull_requests()

        self.assertEqual(len(pull_requests), 1)
        self.assertEqual(pull_requests[0].number, 42)
        self.assertEqual(pull_requests[0].head_ref, "feature/coupon-validation")
        request = client.get.await_args
        self.assertEqual(request.kwargs["params"]["state"], "all")
        self.assertEqual(request.kwargs["headers"]["Authorization"], "Bearer test-token")

    async def test_rejects_github_authentication_failure(self) -> None:
        response = httpx.Response(401)
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.get.return_value = response
        service = GitHubDiffService(owner="example", repo="shop", token="test-token")

        with (
            patch(
                "quality_assistance_backend.services.github_diff_service.httpx.AsyncClient",
                return_value=client,
            ),
            self.assertRaises(HTTPException) as raised,
        ):
            await service.list_pull_requests()

        self.assertEqual(raised.exception.status_code, 401)
        self.assertIn("Update it in Settings", raised.exception.detail)

    async def test_surfaces_github_transport_failure_as_gateway_error(self) -> None:
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        client.get.side_effect = httpx.ConnectError("network unavailable")
        service = GitHubDiffService(owner="example", repo="shop", token="test-token")

        with (
            patch(
                "quality_assistance_backend.services.github_diff_service.httpx.AsyncClient",
                return_value=client,
            ),
            self.assertRaises(HTTPException) as raised,
        ):
            await service.list_pull_requests()

        self.assertEqual(raised.exception.status_code, 502)
        self.assertIn("reach GitHub", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
