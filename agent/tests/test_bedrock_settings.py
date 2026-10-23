import unittest

from app.config.settings import Settings


class BedrockCredentialSettingsTests(unittest.TestCase):
    def test_accepts_local_aws_profile(self) -> None:
        settings = Settings(
            _env_file=None,
            AGENT_BACKEND="bedrock",
            AGENT_MODEL="anthropic.claude-haiku-4-5-20251001-v1:0",
            AWS_PROFILE="test-sso-profile",
        )
        self.assertIsNone(settings.validate_model_credentials())
        self.assertEqual(settings.resolved_model, "bedrock/anthropic.claude-haiku-4-5-20251001-v1:0")

    def test_accepts_ecs_task_role_configuration(self) -> None:
        settings = Settings(
            _env_file=None,
            AGENT_BACKEND="bedrock",
            AWS_USE_IAM_ROLE=True,
        )
        self.assertIsNone(settings.validate_model_credentials())

    def test_rejects_missing_bedrock_credentials(self) -> None:
        settings = Settings(_env_file=None, AGENT_BACKEND="bedrock")
        self.assertIsNotNone(settings.validate_model_credentials())


if __name__ == "__main__":
    unittest.main()
