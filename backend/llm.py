from typing import List, Dict


def build_context_snippet(chunks: List[Dict]) -> str:
    parts = []
    for c in chunks:
        meta = f"(source: {c.get('source', 'unknown')}, chunk: {c.get('chunk_id', 0)})"
        parts.append(meta + "\n" + c["text"])
    return "\n\n---\n\n".join(parts)


def ask_llm_hr(question: str, context_chunks: List[Dict]) -> str:
    """
    Offline, non-LLM version:
    - Takes the top retrieved chunks.
    - Builds a helpful answer by quoting the most relevant policy text.
    """
    if not context_chunks:
        return (
            "I could not find any relevant information about this question in the "
            "uploaded HR documents. Please contact the HR team for clarification."
        )

    top = context_chunks[0]
    source = top.get("source", "HR policy document")

    answer_lines = [
        f"Here is the most relevant information I found in **{source}**:",
        "",
        top["text"],
        "",
        "_(If this does not fully answer your question, please reach out to HR for more details.)_",
    ]

    return "\n".join(answer_lines)
