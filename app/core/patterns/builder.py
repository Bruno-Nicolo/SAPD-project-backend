from app.core.patterns.composite import SimpleComponent, CompositeProduct


class SustainableProductBuilder:
    def __init__(self):
        self._product: CompositeProduct | None = None

    def start_new_product(self, name: str) -> "SustainableProductBuilder":
        self._product = CompositeProduct(name)
        return self

    def add_fabric(
        self,
        name: str,
        material: str,
        weight_kg: float,
        environmental_impact: float,
    ) -> "SustainableProductBuilder":
        if self._product is None:
            raise BuilderError("Must call start_new_product first")
        component = SimpleComponent(name, material, weight_kg, environmental_impact)
        self._product.add(component)
        return self

    def add_lining(
        self,
        name: str,
        material: str,
        weight_kg: float,
        environmental_impact: float,
    ) -> "SustainableProductBuilder":
        if self._product is None:
            raise BuilderError("Must call start_new_product first")
        component = SimpleComponent(name, material, weight_kg, environmental_impact)
        self._product.add(component)
        return self

    def add_accessory(
        self,
        name: str,
        material: str,
        weight_kg: float,
        environmental_impact: float,
    ) -> "SustainableProductBuilder":
        if self._product is None:
            raise BuilderError("Must call start_new_product first")
        component = SimpleComponent(name, material, weight_kg, environmental_impact)
        self._product.add(component)
        return self

    def build(self) -> CompositeProduct:
        if self._product is None:
            raise BuilderError("Must call start_new_product first")
        result = self._product
        self._product = None
        return result


class BuilderError(Exception):
    pass
