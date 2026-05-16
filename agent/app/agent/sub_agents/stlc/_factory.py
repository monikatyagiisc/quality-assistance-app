from google.adk.agents import Agent

from app.utils.llm import resolve_model


def build_stlc_agent(*, name: str, description: str, instruction: str) -> Agent:
    return Agent(
        model=resolve_model(),
        name=name,
        description=description,
        instruction=instruction,
    )
