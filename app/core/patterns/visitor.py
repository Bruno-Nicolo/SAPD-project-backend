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
        line = f"  - Component: {component.name:<20} | Material: {component.material:<20} | Weight: {component.weight_kg:.2f} kg"
        self.report_lines.append(line)

    def visit_composite_product(self, product: CompositeProduct) -> None:
        line = f"Product Report: {product.name}\n" + "-" * 60
        self.report_lines.append(line)

    def get_report(self) -> str:
        return "\n".join(self.report_lines)