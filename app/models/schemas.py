from pydantic import BaseModel


class ComponentCreate(BaseModel):
    """Input schema for creating a component (user provides these fields)."""
    name: str
    material: str
    weight_kg: float
    energy_consumption_mj: float | None = 0.0
    water_usage_liters: float | None = 0.0
    waste_generation_kg: float | None = 0.0
    recyclability_score: float | None = 0.0
    recycled_content_percentage: float | None = 0.0


class ComponentResponse(BaseModel):
    """Output schema for component data (includes calculated impact)."""
    name: str
    material: str
    weight_kg: float
    environmental_impact: float  # Calculated based on material
    energy_consumption_mj: float
    water_usage_liters: float
    waste_generation_kg: float
    recyclability_score: float
    recycled_content_percentage: float


class ProductCreate(BaseModel):
    name: str
    components: list[ComponentCreate]
    badges: list[str] | None = []  # Optional: fairtrade, vegan, oekotex, non_compliant


class ScoringRequest(BaseModel):
    strategy: str
    custom_weights: dict[str, float] | None = None


class WeightUpdate(BaseModel):
    weights: dict[str, float]


class ProductResponse(BaseModel):
    id: int | None = None
    name: str
    average_score: float | None = None
    badges: list[str] = []
    components: list[ComponentResponse]


class ScoreResponse(BaseModel):
    strategy: str
    score: float


class HealthResponse(BaseModel):
    status: str

