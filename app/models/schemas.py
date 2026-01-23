from pydantic import BaseModel


class ComponentCreate(BaseModel):
    name: str
    material: str
    weight_kg: float
    environmental_impact: float


class ProductCreate(BaseModel):
    name: str
    components: list[ComponentCreate]


class BadgeApply(BaseModel):
    badge_type: str


class ScoringRequest(BaseModel):
    strategy: str


class WeightUpdate(BaseModel):
    weights: dict[str, float]


class ScorecardCreate(BaseModel):
    product_name: str
    score: float


class ProductResponse(BaseModel):
    id: int | None = None
    name: str
    total_impact: float
    components: list[ComponentCreate]


class ScoreResponse(BaseModel):
    strategy: str
    score: float


class ScorecardResponse(BaseModel):
    scorecard_id: str
    product_name: str
    score: float
    state: str


class HealthResponse(BaseModel):
    status: str
