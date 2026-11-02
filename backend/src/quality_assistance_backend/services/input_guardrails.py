import re

from fastapi import HTTPException

from quality_assistance_backend.schemas import AssistanceInput

STLC_CONTEXT_PATTERN = re.compile(
    r"\b(?:"
    r"stlc|software testing|quality engineering|quality assurance|qa|"
    r"test case|test data|test plan|test suite|test run|test result|"
    r"test automation|automated test|regression test|acceptance test|"
    r"test coverage|defect|bug report|release readiness|release risk"
    r")\b",
    re.IGNORECASE,
)

SOFTWARE_CONTEXT_PATTERN = re.compile(
    r"\b(?:"
    r"software|application|app|website|web|mobile|system|api|endpoint|service|"
    r"repository|repo|code|diff|pull request|branch|commit|jira|user stor(?:y|ies)|"
    r"acceptance criteria|requirement|feature|database|browser|frontend|backend|"
    r"login|sign[ -]?in|password|account|checkout|cart|payment|order|subscription|"
    r"screen|page|form|button|session|token|deploy|deployment|ci/?cd|pipeline"
    r")\b",
    re.IGNORECASE,
)

OUT_OF_SCOPE_MESSAGE = (
    "This application supports software testing and quality-engineering work. "
    "Include software context such as a requirement, user story, code change, test "
    "result, defect, or release question."
)


def validate_stlc_scope(payload: AssistanceInput) -> None:
    submitted_text = "\n".join(
        value
        for value in (
            payload.requirements,
            payload.user_stories,
            payload.code_diffs,
        )
        if value
    )
    if not (
        SOFTWARE_CONTEXT_PATTERN.search(submitted_text)
        or STLC_CONTEXT_PATTERN.search(submitted_text)
    ):
        raise HTTPException(
            status_code=422,
            detail={"message": OUT_OF_SCOPE_MESSAGE, "code": "out_of_scope"},
        )
