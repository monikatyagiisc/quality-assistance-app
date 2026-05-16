from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from app.callbacks.helpers import content_to_text, context_fields, safe_json, truncate
from app.config.logging_config import get_logger

logger = get_logger(__name__)


def before_agent_log(*, callback_context: CallbackContext) -> types.Content | None:
    fields = context_fields(callback_context)
    logger.info(
        "agent.start agent=%(agent)s user_id=%(user_id)s invocation_id=%(invocation_id)s "
        "session_id=%(session_id)s",
        fields,
    )
    if callback_context.user_content:
        logger.debug(
            "agent.input user_content=%s",
            content_to_text(callback_context.user_content),
        )
    return None


def after_agent_log(*, callback_context: CallbackContext) -> types.Content | None:
    logger.info(
        "agent.end agent=%(agent)s user_id=%(user_id)s invocation_id=%(invocation_id)s "
        "session_id=%(session_id)s",
        context_fields(callback_context),
    )
    return None


def before_model_log(
    *,
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> LlmResponse | None:
    logger.info(
        "model.request agent=%(agent)s user_id=%(user_id)s invocation_id=%(invocation_id)s model=%s",
        context_fields(callback_context),
        llm_request.model or "default",
    )
    logger.debug("model.request.payload=%s", truncate(repr(llm_request)))
    return None


def after_model_log(
    *,
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    logger.info(
        "model.response agent=%(agent)s user_id=%(user_id)s invocation_id=%(invocation_id)s",
        context_fields(callback_context),
    )
    if llm_response.error_code:
        logger.warning(
            "model.response.error code=%s message=%s",
            llm_response.error_code,
            llm_response.error_message,
        )
    logger.debug("model.response.payload=%s", truncate(repr(llm_response)))
    return None


def on_model_error_log(
    *,
    callback_context: CallbackContext,
    llm_request: LlmRequest,
    error: Exception,
) -> LlmResponse | None:
    logger.error(
        "model.error agent=%(agent)s user_id=%(user_id)s invocation_id=%(invocation_id)s error=%s",
        context_fields(callback_context),
        str(error),
        exc_info=error,
    )
    return None


def before_tool_log(
    *,
    tool: BaseTool,
    args: dict[str, object],
    tool_context: ToolContext,
) -> dict | None:
    fields = context_fields(tool_context)
    logger.info(
        "tool.start tool=%s agent=%(agent)s user_id=%(user_id)s invocation_id=%(invocation_id)s args=%s",
        tool.name,
        fields,
        safe_json(args, limit=1200),
    )
    return None


def after_tool_log(
    *,
    tool: BaseTool,
    args: dict[str, object],
    tool_context: ToolContext,
    tool_response: dict,
) -> dict | None:
    fields = context_fields(tool_context)
    logger.info(
        "tool.end tool=%s agent=%(agent)s user_id=%(user_id)s invocation_id=%(invocation_id)s response=%s",
        tool.name,
        fields,
        safe_json(tool_response, limit=1200),
    )
    return None


def on_tool_error_log(
    *,
    tool: BaseTool,
    args: dict[str, object],
    tool_context: ToolContext,
    error: Exception,
) -> dict | None:
    fields = context_fields(tool_context)
    logger.error(
        "tool.error tool=%s agent=%(agent)s user_id=%(user_id)s invocation_id=%(invocation_id)s "
        "args=%s error=%s",
        tool.name,
        fields,
        safe_json(args, limit=800),
        error,
        exc_info=error,
    )
    return None


AGENT_LOG_CALLBACKS = {
    "before_agent_callback": before_agent_log,
    "after_agent_callback": after_agent_log,
    "before_model_callback": before_model_log,
    "after_model_callback": after_model_log,
    "on_model_error_callback": on_model_error_log,
    "before_tool_callback": before_tool_log,
    "after_tool_callback": after_tool_log,
    "on_tool_error_callback": on_tool_error_log,
}
