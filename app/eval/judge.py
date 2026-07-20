"""LLM-as-judge for answer quality (faithfulness & relevancy)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.llm import LLMProvider, system, user
from app.rag.prompts import JUDGE_SYSTEM_PROMPT, build_judge_prompt

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class JudgeResult:
    faithfulness: float
    answer_relevancy: float
    reasoning: str


def _extract_json(text: str) -> dict:
    match = _JSON_RE.search(text)
    if not match:
        raise ValueError(f"Judge did not return JSON: {text!r}")
    return json.loads(match.group(0))


def _clamp(value: object) -> float:
    try:
        return max(0.0, min(1.0, float(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


class AnswerJudge:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    def evaluate(
        self, question: str, answer: str, contexts: list[str]
    ) -> JudgeResult:
        messages = [
            system(JUDGE_SYSTEM_PROMPT),
            user(build_judge_prompt(question, answer, contexts)),
        ]
        raw = self._llm.generate(messages, temperature=0.0, max_tokens=400)
        data = _extract_json(raw)
        return JudgeResult(
            faithfulness=_clamp(data.get("faithfulness")),
            answer_relevancy=_clamp(data.get("answer_relevancy")),
            reasoning=str(data.get("reasoning", "")),
        )
