from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.patterns.composite import SimpleComponent, CompositeProduct


class ProductVisitor(ABC):
    @abstractmethod
    def visit_simple_component(self, component: SimpleComponent) -> None:
        pass

    @abstractmethod
    def visit_composite_product(self, product: CompositeProduct) -> None:
        pass


class PdfReportVisitor(ProductVisitor):
    """Visitor that collects structured data for PDF report generation.
    
    This visitor traverses the product composite structure and collects
    all necessary data for generating a sustainability report PDF.
    """
    
    def __init__(self):
        self.products: list[dict] = []
        self._current_product: dict | None = None

    def visit_simple_component(self, component: SimpleComponent) -> None:
        """Visit a simple component and collect its data."""
        if self._current_product is None:
            return
            
        component_data = {
            "name": component.name,
            "material": component.material,
            "weight_kg": component.weight_kg,
            "environmental_impact": component.environmental_impact,
            "energy_consumption_mj": component.energy_consumption_mj,
            "water_usage_liters": component.water_usage_liters,
            "waste_generation_kg": component.waste_generation_kg,
            "recyclability_score": component.recyclability_score,
            "recycled_content_percentage": component.recycled_content_percentage,
        }
        self._current_product["components"].append(component_data)

    def visit_composite_product(self, product: CompositeProduct) -> None:
        """Visit a composite product and initialize its data collection."""
        self._current_product = {
            "name": product.name,
            "components": [],
            "impact_factors": product.get_impact_factors(),
        }
        self.products.append(self._current_product)

    def get_products_data(self) -> list[dict]:
        """Return the collected products data for PDF generation."""
        return self.products
    
    def get_report(self) -> str:
        """Return a text-based report (for backward compatibility)."""
        lines = []
        for product in self.products:
            lines.append(f"Product Report: {product['name']}")
            lines.append("-" * 60)
            for comp in product["components"]:
                lines.append(
                    f"  - Component: {comp['name']:<20} | "
                    f"Material: {comp['material']:<20} | "
                    f"Weight: {comp['weight_kg']:.2f} kg"
                )
            lines.append("")
        return "\n".join(lines)