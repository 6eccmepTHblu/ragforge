"""Evaluation endpoint: LLM-as-judge for a single answer."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import Container, get_container
from app.schemas import JudgeRequest, JudgeResponse

router = APIRouter(prefix="/eval", tags=["evaluation"])


@router.post("/judge", response_model=JudgeResponse)
def judge(
    payload: JudgeRequest, container: Container = Depends(get_container)
) -> JudgeResponse:
    result = container.judge.evaluate(
        question=payload.question, answer=payload.answer, contexts=payload.contexts
    )
    return JudgeResponse(
        faithfulness=result.faithfulness,
        answer_relevancy=result.answer_relevancy,
        reasoning=result.reasoning,
    )
