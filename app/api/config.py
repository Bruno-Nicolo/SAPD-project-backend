from fastapi import APIRouter

from app.models.schemas import WeightUpdate
from app.core.patterns.observer import WeightConfigSubject, ScoringModule

router = APIRouter(prefix="/config", tags=["configuration"])

weight_config = WeightConfigSubject()

higg_module = ScoringModule("higg_index")
carbon_module = ScoringModule("carbon_footprint")
circular_module = ScoringModule("circular_economy")

weight_config.attach(higg_module)
weight_config.attach(carbon_module)
weight_config.attach(circular_module)

weights_store: dict[str, float] = {
    "material_sustainability": 0.3,
    "carbon_footprint": 0.25,
    "water_usage": 0.2,
    "social_impact": 0.15,
    "circularity": 0.1,
}


@router.get("/weights")
def get_weights():
    """Get current weight configuration."""
    return {"weights": weights_store}


@router.put("/weights")
def update_weights(weight_data: WeightUpdate):
    """Update weight configuration."""
    for criterion, new_weight in weight_data.weights.items():
        weights_store[criterion] = new_weight

    weight_config.set_weights(weights_store)

    return {"message": "Weights updated", "weights": weights_store}
