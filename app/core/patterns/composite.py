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
    def accept(self, visitor: ProductVisitor) -> None:
        pass

    @abstractmethod
    def get_impact_factors(self) -> dict[str, float]:
        pass

class SimpleComponent(ProductComponent):
    def __init__(
        self,
        name: str,
        material: str,
        weight_kg: float,
        environmental_impact: float,
        energy_consumption_mj: float = 0.0,
        water_usage_liters: float = 0.0,
        waste_generation_kg: float = 0.0,
        recyclability_score: float = 0.0,
        recycled_content_percentage: float = 0.0,
    ):
        super().__init__(name, material, weight_kg)
        self.environmental_impact = environmental_impact
        self.energy_consumption_mj = energy_consumption_mj
        self.water_usage_liters = water_usage_liters
        self.waste_generation_kg = waste_generation_kg
        self.recyclability_score = recyclability_score
        self.recycled_content_percentage = recycled_content_percentage

    
    def get_impact_factors(self) -> dict[str, float]:
        """Return raw impact factors for exact calculations."""
        return {
            "energy": self.energy_consumption_mj,
            "water": self.water_usage_liters,
            "waste": self.waste_generation_kg,
            "recyclability": self.recyclability_score,
            "recycled_content": self.recycled_content_percentage,
            "weight_kg": self.weight_kg,
        }

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


    def get_impact_factors(self) -> dict[str, float]:
        """Aggregate impact factors from children."""
        total_energy = 0.0
        total_water = 0.0
        total_waste = 0.0
        weighted_recyclability = 0.0
        weighted_recycled_content = 0.0
        total_weight = 0.0

        for child in self._children:
            factors = child.get_impact_factors()
            w = factors.get("weight_kg", 0.0)
            
            total_energy += factors.get("energy", 0.0)
            total_water += factors.get("water", 0.0)
            total_waste += factors.get("waste", 0.0)
            
            # Weighted averages
            weighted_recyclability += factors.get("recyclability", 0.0) * w
            weighted_recycled_content += factors.get("recycled_content", 0.0) * w
            
            total_weight += w
        
        if total_weight > 0:
            avg_recyclability = weighted_recyclability / total_weight
            avg_recycled_content = weighted_recycled_content / total_weight
        else:
            avg_recyclability = 0.0
            avg_recycled_content = 0.0

        return {
            "energy": total_energy,
            "water": total_water,
            "waste": total_waste,
            "recyclability": avg_recyclability,
            "recycled_content": avg_recycled_content,
            "weight_kg": total_weight,
        }

    def accept(self, visitor: ProductVisitor) -> None:
        visitor.visit_composite_product(self)
        for child in self._children:
            child.accept(visitor)
