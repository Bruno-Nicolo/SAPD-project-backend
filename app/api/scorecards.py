from fastapi import APIRouter, HTTPException
import uuid

from app.models.schemas import ScorecardCreate, ScorecardResponse
from app.core.patterns.state import Scorecard, InvalidStateTransitionError

router = APIRouter(prefix="/scorecards", tags=["scorecards"])

scorecards_db: dict[str, Scorecard] = {}


@router.post("/", response_model=ScorecardResponse)
def create_scorecard(scorecard_data: ScorecardCreate):
    scorecard_id = str(uuid.uuid4())
    scorecard = Scorecard(
        scorecard_id=scorecard_id,
        product_name=scorecard_data.product_name,
        score=scorecard_data.score,
    )
    scorecards_db[scorecard_id] = scorecard

    return ScorecardResponse(
        scorecard_id=scorecard_id,
        product_name=scorecard.product_name,
        score=scorecard.score,
        state=scorecard.get_state_name(),
    )


@router.get("/{scorecard_id}", response_model=ScorecardResponse)
def get_scorecard(scorecard_id: str):
    if scorecard_id not in scorecards_db:
        raise HTTPException(status_code=404, detail="Scorecard not found")

    scorecard = scorecards_db[scorecard_id]
    return ScorecardResponse(
        scorecard_id=scorecard_id,
        product_name=scorecard.product_name,
        score=scorecard.score,
        state=scorecard.get_state_name(),
    )


@router.post("/{scorecard_id}/submit-review", response_model=ScorecardResponse)
def submit_for_review(scorecard_id: str):
    if scorecard_id not in scorecards_db:
        raise HTTPException(status_code=404, detail="Scorecard not found")

    scorecard = scorecards_db[scorecard_id]
    try:
        scorecard.submit_for_review()
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ScorecardResponse(
        scorecard_id=scorecard_id,
        product_name=scorecard.product_name,
        score=scorecard.score,
        state=scorecard.get_state_name(),
    )


@router.post("/{scorecard_id}/certify", response_model=ScorecardResponse)
def certify_scorecard(scorecard_id: str):
    if scorecard_id not in scorecards_db:
        raise HTTPException(status_code=404, detail="Scorecard not found")

    scorecard = scorecards_db[scorecard_id]
    try:
        scorecard.certify()
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ScorecardResponse(
        scorecard_id=scorecard_id,
        product_name=scorecard.product_name,
        score=scorecard.score,
        state=scorecard.get_state_name(),
    )


@router.post("/{scorecard_id}/deprecate", response_model=ScorecardResponse)
def deprecate_scorecard(scorecard_id: str):
    if scorecard_id not in scorecards_db:
        raise HTTPException(status_code=404, detail="Scorecard not found")

    scorecard = scorecards_db[scorecard_id]
    try:
        scorecard.deprecate()
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ScorecardResponse(
        scorecard_id=scorecard_id,
        product_name=scorecard.product_name,
        score=scorecard.score,
        state=scorecard.get_state_name(),
    )


@router.post("/{scorecard_id}/edit", response_model=ScorecardResponse)
def edit_scorecard(scorecard_id: str):
    if scorecard_id not in scorecards_db:
        raise HTTPException(status_code=404, detail="Scorecard not found")

    scorecard = scorecards_db[scorecard_id]
    try:
        scorecard.edit()
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ScorecardResponse(
        scorecard_id=scorecard_id,
        product_name=scorecard.product_name,
        score=scorecard.score,
        state=scorecard.get_state_name(),
    )
