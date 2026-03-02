"""Sentence-level evidence extraction for skill highlighting.

Deterministic, LLM-free. Given resume text and a list of skills, returns
a mapping of each skill to up to 2 sentence snippets where it appears.
"""

import re
from typing import Dict, List

# Max characters per evidence snippet before truncation.
_MAX_SNIPPET_LEN = 200

# Sentence splitter: split on .!? or newline, keeping the delimiter with the
# preceding text. Handles common abbreviations poorly but is good enough for
# resume text which rarely uses complex punctuation.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def _split_sentences(text: str) -> List[str]:
    """Split text into sentence-like chunks."""
    parts = _SENTENCE_RE.split(text)
    return [s.strip() for s in parts if s.strip()]


def _truncate(sentence: str) -> str:
    """Truncate a sentence to ~_MAX_SNIPPET_LEN chars at a word boundary."""
    if len(sentence) <= _MAX_SNIPPET_LEN:
        return sentence
    # Find last space before the limit.
    idx = sentence.rfind(" ", 0, _MAX_SNIPPET_LEN)
    if idx == -1:
        idx = _MAX_SNIPPET_LEN
    return sentence[:idx] + "..."


def _build_pattern(skill: str) -> re.Pattern[str]:
    """Build a case-insensitive regex for a skill with word boundaries.

    Handles:
    - Special chars like c++, c# (re.escape)
    - Multi-word skills ("machine learning") — flexible whitespace
    - Word boundaries skipped at ends with non-alphanumeric chars
    """
    words = skill.strip().split()
    escaped = [re.escape(w) for w in words]
    inner = r"\s+".join(escaped)

    # Only add \b at start/end if the boundary character is alphanumeric.
    prefix = r"\b" if words[0][0].isalnum() else ""
    suffix = r"\b" if words[-1][-1].isalnum() else ""

    return re.compile(prefix + inner + suffix, re.IGNORECASE)


def extract_evidence(resume_text: str, skills: List[str]) -> Dict[str, List[str]]:
    """Extract up to 2 sentence-level evidence snippets per skill.

    Args:
        resume_text: The original plain-text resume.
        skills: List of skill strings to search for (lowercase).

    Returns:
        Dict mapping each skill to a list of 0–2 truncated snippets.
    """
    if not resume_text or not resume_text.strip():
        return {skill: [] for skill in skills}

    sentences = _split_sentences(resume_text)
    result: Dict[str, List[str]] = {}

    for skill in skills:
        pattern = _build_pattern(skill)
        snippets: List[str] = []
        seen: set[str] = set()

        for sentence in sentences:
            if len(snippets) >= 2:
                break
            if pattern.search(sentence):
                truncated = _truncate(sentence)
                if truncated not in seen:
                    snippets.append(truncated)
                    seen.add(truncated)

        result[skill] = snippets

    return result
