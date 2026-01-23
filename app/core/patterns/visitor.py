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
    def __init__(self):
        self.report_lines: list[str] = []

    def visit_simple_component(self, component: SimpleComponent) -> None:
        line = f"Component: {component.name} | Material: {component.material} | Impact: {component.get_base_impact_score():.2f}"
        self.report_lines.append(line)

    def visit_composite_product(self, product: CompositeProduct) -> None:
        line = f"Product: {product.name} | Total Impact: {product.get_base_impact_score():.2f}"
        self.report_lines.append(line)

    def get_report(self) -> str:
        return "\n".join(self.report_lines)


class ComplianceAuditVisitor(ProductVisitor):
    NON_COMPLIANT_MATERIALS = {"pvc", "conventional_cotton", "virgin_polyester"}

    def __init__(self):
        self.issues: list[str] = []

    def visit_simple_component(self, component: SimpleComponent) -> None:
        if component.material.lower() in self.NON_COMPLIANT_MATERIALS:
            self.issues.append(f"Non-compliant material in '{component.name}': {component.material}")

    def visit_composite_product(self, product: CompositeProduct) -> None:
        pass

    def is_compliant(self) -> bool:
        return len(self.issues) == 0

    def get_audit_report(self) -> dict:
        return {"compliant": self.is_compliant(), "issues": self.issues}


class SocialReportVisitor(ProductVisitor):
    def __init__(self):
        self.total_weight_kg = 0.0
        self.total_impact = 0.0
        self.component_count = 0

    def visit_simple_component(self, component: SimpleComponent) -> None:
        self.total_weight_kg += component.weight_kg
        self.total_impact += component.get_base_impact_score()
        self.component_count += 1

    def visit_composite_product(self, product: CompositeProduct) -> None:
        pass

    def get_social_report(self) -> dict:
        return {
            "total_weight_kg": self.total_weight_kg,
            "total_impact": self.total_impact,
            "component_count": self.component_count,
        }
