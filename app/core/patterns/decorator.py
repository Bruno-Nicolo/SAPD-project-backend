from abc import ABC, abstractmethod

from app.core.patterns.composite import ProductComponent


class ProductDecorator(ProductComponent, ABC):
    def __init__(self, wrapped: ProductComponent):
        super().__init__(wrapped.name, wrapped.material, wrapped.weight_kg)
        self._wrapped = wrapped

    @abstractmethod
    def get_score_modifier(self) -> float:
        pass

    def get_impact_factors(self) -> dict[str, float]:
        return self._wrapped.get_impact_factors()


    def accept(self, visitor) -> None:
        self._wrapped.accept(visitor)


class FairTradeBadge(ProductDecorator):
    SCORE_BONUS = -5.0

    def get_score_modifier(self) -> float:
        return self.SCORE_BONUS


class VeganBadge(ProductDecorator):
    SCORE_BONUS = -3.0

    def get_score_modifier(self) -> float:
        return self.SCORE_BONUS


class OekoTexBadge(ProductDecorator):
    SCORE_BONUS = -4.0

    def get_score_modifier(self) -> float:
        return self.SCORE_BONUS


class NonCompliantBadge(ProductDecorator):
    SCORE_PENALTY = 10.0

    def get_score_modifier(self) -> float:
        return self.SCORE_PENALTY
