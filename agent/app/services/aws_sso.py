import logging
import shutil
import subprocess
from threading import Lock

from app.config.settings import settings

logger = logging.getLogger(__name__)

_login_lock = Lock()
_login_process: subprocess.Popen[bytes] | None = None


def is_expired_aws_sso_token(exc: BaseException) -> bool:
    pending: list[BaseException] = [exc]
    visited: set[int] = set()
    error_text = ""

    while pending:
        current = pending.pop()
        if id(current) in visited:
            continue
        visited.add(id(current))
        error_text += f" {type(current).__name__} {current}"
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)

    normalized = error_text.upper()
    return "TOKENRETRIEVALERROR" in normalized and (
        "TOKEN HAS EXPIRED" in normalized or "REFRESH FAILED" in normalized
    )


def start_aws_sso_login(exc: BaseException) -> bool:
    global _login_process

    if (
        settings.agent_backend != "bedrock"
        or not settings.aws_profile
        or settings.aws_use_iam_role
        or settings.aws_access_key_id
        or settings.aws_secret_access_key
        or settings.aws_session_token
        or not is_expired_aws_sso_token(exc)
    ):
        return False

    aws_cli = shutil.which("aws")
    if not aws_cli:
        logger.error("aws_sso.login_unavailable reason=aws_cli_not_found")
        return False

    with _login_lock:
        if _login_process is not None and _login_process.poll() is None:
            logger.info("aws_sso.login_already_running profile=%s", settings.aws_profile)
            return True

        try:
            _login_process = subprocess.Popen(
                [aws_cli, "sso", "login", "--profile", settings.aws_profile],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError:
            logger.exception("aws_sso.login_start_failed profile=%s", settings.aws_profile)
            _login_process = None
            return False

    logger.warning("aws_sso.login_started profile=%s", settings.aws_profile)
    return True
