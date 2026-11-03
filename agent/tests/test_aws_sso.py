import unittest
from unittest.mock import Mock, patch

from app.errors import classify_agent_error
from app.services import aws_sso


class TokenRetrievalError(Exception):
    pass


class AwsSsoRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        aws_sso._login_process = None

    def tearDown(self) -> None:
        aws_sso._login_process = None

    def test_detects_expired_token_in_exception_cause(self) -> None:
        try:
            try:
                raise TokenRetrievalError("Token has expired and refresh failed")
            except TokenRetrievalError as cause:
                raise RuntimeError("model request failed") from cause
        except RuntimeError as exc:
            self.assertTrue(aws_sso.is_expired_aws_sso_token(exc))

    def test_does_not_detect_other_credential_errors(self) -> None:
        self.assertFalse(aws_sso.is_expired_aws_sso_token(RuntimeError("access denied")))

    @patch.object(aws_sso.settings, "agent_backend", "bedrock")
    @patch.object(aws_sso.settings, "aws_profile", "test-sso-profile")
    @patch("app.services.aws_sso.shutil.which", return_value="/usr/bin/aws")
    @patch("app.services.aws_sso.subprocess.Popen")
    def test_starts_login_once_for_configured_profile(
        self,
        popen: Mock,
        _which: Mock,
    ) -> None:
        process = Mock()
        process.poll.return_value = None
        popen.return_value = process
        exc = TokenRetrievalError("Token has expired and refresh failed")

        self.assertTrue(aws_sso.start_aws_sso_login(exc))
        self.assertTrue(aws_sso.start_aws_sso_login(exc))

        popen.assert_called_once_with(
            ["/usr/bin/aws", "sso", "login", "--profile", "test-sso-profile"],
            stdin=aws_sso.subprocess.DEVNULL,
            stdout=aws_sso.subprocess.DEVNULL,
            stderr=aws_sso.subprocess.DEVNULL,
            start_new_session=True,
        )

    @patch.object(aws_sso.settings, "agent_backend", "bedrock")
    @patch.object(aws_sso.settings, "aws_profile", "test-sso-profile")
    @patch("app.services.aws_sso.shutil.which", return_value=None)
    @patch("app.services.aws_sso.subprocess.Popen")
    def test_missing_aws_cli_leaves_manual_recovery_path(
        self,
        popen: Mock,
        _which: Mock,
    ) -> None:
        exc = TokenRetrievalError("Token has expired and refresh failed")

        self.assertFalse(aws_sso.start_aws_sso_login(exc))
        popen.assert_not_called()
        error = classify_agent_error(exc, aws_sso_login_started=False)
        self.assertIn("aws sso login --profile test-sso-profile", error.message)

    @patch.object(aws_sso.settings, "agent_backend", "bedrock")
    @patch.object(aws_sso.settings, "aws_profile", "")
    @patch("app.services.aws_sso.shutil.which")
    @patch("app.services.aws_sso.subprocess.Popen")
    def test_does_not_start_login_without_configured_profile(
        self,
        popen: Mock,
        which: Mock,
    ) -> None:
        exc = TokenRetrievalError("Token has expired and refresh failed")

        self.assertFalse(aws_sso.start_aws_sso_login(exc))
        which.assert_not_called()
        popen.assert_not_called()

    @patch.object(aws_sso.settings, "aws_profile", "test-sso-profile")
    def test_error_message_instructs_retry_after_login(self) -> None:
        exc = TokenRetrievalError("Token has expired and refresh failed")

        error = classify_agent_error(exc, aws_sso_login_started=True)

        self.assertEqual(error.status_code, 503)
        self.assertEqual(error.code, "aws_sso_session_expired")
        self.assertIn("browser login has been started", error.message)
        self.assertIn("then retry", error.message)


if __name__ == "__main__":
    unittest.main()
