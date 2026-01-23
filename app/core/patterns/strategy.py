from abc import ABC, abstractmethod

from app.core.patterns.composite import ProductComponent


class ScoringStrategy(ABC):
    @abstractmethod
    def calculate_score(self, component: ProductComponent) -> float:
        pass


class HiggIndexStrategy(ScoringStrategy):
    def calculate_score(self, component: ProductComponent) -> float:
        base_score = component.get_base_impact_score()
        return max(0, 100 - base_score * 10)


class CarbonFootprintStrategy(ScoringStrategy):
    def calculate_score(self, component: ProductComponent) -> float:
        base_score = component.get_base_impact_score()
        return base_score * 2.5


class CircularEconomyStrategy(ScoringStrategy):
    RECYCLABLE_MATERIALS = {"cotton", "wool", "linen", "hemp", "recycled_polyester"}

    def calculate_score(self, component: ProductComponent) -> float:
        base_score = component.get_base_impact_score()
        material_bonus = 20 if component.material.lower() in self.RECYCLABLE_MATERIALS else 0
        return max(0, 100 - base_score * 5 + material_bonus)


class ScoringContext:
    def __init__(self, strategy: ScoringStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: ScoringStrategy) -> None:
        self._strategy = strategy

    def calculate(self, component: ProductComponent) -> float:
        return self._strategy.calculate_score(component)
