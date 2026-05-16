def build_instruction(instruction: str, examples: str = "") -> str:
    if examples.strip():
        return f"{instruction}\n\n## Examples\n\n{examples.strip()}"
    return instruction
