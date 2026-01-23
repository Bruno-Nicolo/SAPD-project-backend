from fastapi import APIRouter

from app.models.schemas import WeightUpdate
from app.core.patterns.observer import WeightConfigSubject, ScoringModule
from app.core.patterns.command import CommandHistory, UpdateWeightCommand

router = APIRouter(prefix="/config", tags=["configuration"])

weight_config = WeightConfigSubject()
command_history = CommandHistory()

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
    return {"weights": weights_store}


@router.put("/weights")
def update_weights(weight_data: WeightUpdate):
    for criterion, new_weight in weight_data.weights.items():
        old_weight = weights_store.get(criterion)
        command = UpdateWeightCommand(weights_store, criterion, new_weight)
        command_history.execute(command)

    weight_config.set_weights(weights_store)

    return {"message": "Weights updated", "weights": weights_store}


@router.post("/weights/undo")
def undo_weight_change():
    success = command_history.undo()
    if not success:
        return {"message": "Nothing to undo", "weights": weights_store}

    weight_config.set_weights(weights_store)
    return {"message": "Undo successful", "weights": weights_store}


@router.post("/weights/redo")
def redo_weight_change():
    success = command_history.redo()
    if not success:
        return {"message": "Nothing to redo", "weights": weights_store}

    weight_config.set_weights(weights_store)
    return {"message": "Redo successful", "weights": weights_store}


@router.get("/weights/history")
def get_weight_history():
    return {"history": command_history.get_history_log()}
