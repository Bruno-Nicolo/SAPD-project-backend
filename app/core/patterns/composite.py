from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.patterns.visitor import ProductVisitor


class ProductComponent(ABC):
    def __init__(self, name: str, material: str, weight_kg: float):
        self.name = name
        self.material = material
        self.weight_kg = weight_kg

    @abstractmethod
    def get_base_impact_score(self) -> float:
        pass

    @abstractmethod
    def accept(self, visitor: ProductVisitor) -> None:
        pass


class SimpleComponent(ProductComponent):
    def __init__(
        self,
        name: str,
        material: str,
        weight_kg: float,
        environmental_impact: float,
    ):
        super().__init__(name, material, weight_kg)
        self.environmental_impact = environmental_impact

    def get_base_impact_score(self) -> float:
        return self.environmental_impact * self.weight_kg

    def accept(self, visitor: ProductVisitor) -> None:
        visitor.visit_simple_component(self)


class CompositeProduct(ProductComponent):
    def __init__(self, name: str, material: str = "composite", weight_kg: float = 0.0):
        super().__init__(name, material, weight_kg)
        self._children: list[ProductComponent] = []

    def add(self, component: ProductComponent) -> None:
        self._children.append(component)

    def remove(self, component: ProductComponent) -> None:
        self._children.remove(component)

    def get_children(self) -> list[ProductComponent]:
        return self._children.copy()

    def get_base_impact_score(self) -> float:
        return sum(child.get_base_impact_score() for child in self._children)

    def accept(self, visitor: ProductVisitor) -> None:
        visitor.visit_composite_product(self)
        for child in self._children:
            child.accept(visitor)
