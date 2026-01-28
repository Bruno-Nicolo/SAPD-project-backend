"""
Unit tests for the Composite Pattern - Products and Components.

Tests cover:
- SimpleComponent: leaf node creation and impact factors
- CompositeProduct: container for components with aggregated metrics
- Hierarchy operations: add, remove, get_children
"""
import pytest
from app.core.patterns.composite import (
    ProductComponent,
    SimpleComponent,
    CompositeProduct,
)


# ============================================================================
# SIMPLE COMPONENT TESTS
# ============================================================================

class TestSimpleComponent:
    """Tests for SimpleComponent (leaf node in composite pattern)."""
    
    def test_creation_with_required_fields(self):
        """SimpleComponent should be created with required fields."""
        component = SimpleComponent(
            name="Test Fabric",
            material="cotton",
            weight_kg=0.5,
            environmental_impact=4.0
        )
        assert component.name == "Test Fabric"
        assert component.material == "cotton"
        assert component.weight_kg == 0.5
        assert component.environmental_impact == 4.0
    
    def test_creation_with_all_fields(self):
        """SimpleComponent should accept all optional fields."""
        component = SimpleComponent(
            name="Complete Component",
            material="organic_cotton",
            weight_kg=1.0,
            environmental_impact=3.0,
            energy_consumption_mj=25.0,
            water_usage_liters=100.0,
            waste_generation_kg=0.1,
            recyclability_score=0.8,
            recycled_content_percentage=0.5
        )
        assert component.energy_consumption_mj == 25.0
        assert component.water_usage_liters == 100.0
        assert component.waste_generation_kg == 0.1
        assert component.recyclability_score == 0.8
        assert component.recycled_content_percentage == 0.5
    
    def test_default_values_for_optional_fields(self):
        """Optional fields should default to 0.0."""
        component = SimpleComponent(
            name="Minimal",
            material="test",
            weight_kg=1.0,
            environmental_impact=1.0
        )
        assert component.energy_consumption_mj == 0.0
        assert component.water_usage_liters == 0.0
        assert component.waste_generation_kg == 0.0
        assert component.recyclability_score == 0.0
        assert component.recycled_content_percentage == 0.0
    
    def test_get_impact_factors(self):
        """get_impact_factors should return correct dictionary."""
        component = SimpleComponent(
            name="Test",
            material="cotton",
            weight_kg=2.0,
            environmental_impact=5.0,
            energy_consumption_mj=30.0,
            water_usage_liters=150.0,
            waste_generation_kg=0.2,
            recyclability_score=0.7,
            recycled_content_percentage=0.4
        )
        factors = component.get_impact_factors()
        
        assert factors["energy"] == 30.0
        assert factors["water"] == 150.0
        assert factors["waste"] == 0.2
        assert factors["recyclability"] == 0.7
        assert factors["recycled_content"] == 0.4
        assert factors["weight_kg"] == 2.0
    
    def test_impact_factors_keys(self):
        """Impact factors should contain all expected keys."""
        component = SimpleComponent(
            name="Test", material="test", weight_kg=1.0, environmental_impact=1.0
        )
        factors = component.get_impact_factors()
        
        expected_keys = {"energy", "water", "waste", "recyclability", "recycled_content", "weight_kg"}
        assert set(factors.keys()) == expected_keys


# ============================================================================
# COMPOSITE PRODUCT TESTS
# ============================================================================

class TestCompositeProduct:
    """Tests for CompositeProduct (container in composite pattern)."""
    
    def test_creation(self):
        """CompositeProduct should be created with a name."""
        product = CompositeProduct(name="Test Product")
        assert product.name == "Test Product"
        assert product.material == "composite"
        assert product.weight_kg == 0.0
    
    def test_add_component(self):
        """Components can be added to the product."""
        product = CompositeProduct(name="Product")
        component = SimpleComponent(
            name="Fabric", material="cotton", weight_kg=0.5, environmental_impact=4.0
        )
        product.add(component)
        
        children = product.get_children()
        assert len(children) == 1
        assert children[0].name == "Fabric"
    
    def test_add_multiple_components(self):
        """Multiple components can be added."""
        product = CompositeProduct(name="Product")
        comp1 = SimpleComponent(name="C1", material="m1", weight_kg=0.3, environmental_impact=3.0)
        comp2 = SimpleComponent(name="C2", material="m2", weight_kg=0.2, environmental_impact=2.0)
        
        product.add(comp1)
        product.add(comp2)
        
        assert len(product.get_children()) == 2
    
    def test_remove_component(self):
        """Components can be removed from the product."""
        product = CompositeProduct(name="Product")
        component = SimpleComponent(
            name="Fabric", material="cotton", weight_kg=0.5, environmental_impact=4.0
        )
        product.add(component)
        product.remove(component)
        
        assert len(product.get_children()) == 0
    
    def test_get_children_returns_copy(self):
        """get_children should return a copy (not modify internal state)."""
        product = CompositeProduct(name="Product")
        component = SimpleComponent(name="C1", material="m1", weight_kg=0.3, environmental_impact=3.0)
        product.add(component)
        
        children = product.get_children()
        children.clear()  # Modify the returned list
        
        # Original should be unchanged
        assert len(product.get_children()) == 1
    
    def test_impact_factors_empty_product(self):
        """Empty product should return zero impact factors."""
        product = CompositeProduct(name="Empty")
        factors = product.get_impact_factors()
        
        assert factors["energy"] == 0.0
        assert factors["water"] == 0.0
        assert factors["waste"] == 0.0
        assert factors["weight_kg"] == 0.0
    
    def test_impact_factors_aggregation(self):
        """Impact factors should aggregate from all children."""
        product = CompositeProduct(name="Product")
        
        comp1 = SimpleComponent(
            name="C1", material="m1", weight_kg=1.0, environmental_impact=3.0,
            energy_consumption_mj=20.0, water_usage_liters=100.0, waste_generation_kg=0.1
        )
        comp2 = SimpleComponent(
            name="C2", material="m2", weight_kg=2.0, environmental_impact=5.0,
            energy_consumption_mj=30.0, water_usage_liters=150.0, waste_generation_kg=0.2
        )
        
        product.add(comp1)
        product.add(comp2)
        
        factors = product.get_impact_factors()
        
        assert factors["energy"] == pytest.approx(50.0)  # 20 + 30
        assert factors["water"] == pytest.approx(250.0)  # 100 + 150
        assert factors["waste"] == pytest.approx(0.3)  # 0.1 + 0.2
        assert factors["weight_kg"] == pytest.approx(3.0)  # 1 + 2
    
    def test_impact_factors_weighted_average_recyclability(self):
        """Recyclability should be weight-averaged."""
        product = CompositeProduct(name="Product")
        
        # Component 1: weight 1kg, recyclability 0.6
        comp1 = SimpleComponent(
            name="C1", material="m1", weight_kg=1.0, environmental_impact=3.0,
            recyclability_score=0.6
        )
        # Component 2: weight 3kg, recyclability 0.8
        comp2 = SimpleComponent(
            name="C2", material="m2", weight_kg=3.0, environmental_impact=5.0,
            recyclability_score=0.8
        )
        
        product.add(comp1)
        product.add(comp2)
        
        factors = product.get_impact_factors()
        
        # Weighted average: (0.6 * 1 + 0.8 * 3) / (1 + 3) = 3.0 / 4 = 0.75
        assert factors["recyclability"] == pytest.approx(0.75)
    
    def test_nested_composite(self):
        """Composite products can contain other composite products."""
        outer = CompositeProduct(name="Outer")
        inner = CompositeProduct(name="Inner")
        
        component = SimpleComponent(
            name="Leaf", material="m1", weight_kg=1.0, environmental_impact=3.0,
            energy_consumption_mj=10.0
        )
        inner.add(component)
        outer.add(inner)
        
        factors = outer.get_impact_factors()
        assert factors["energy"] == 10.0
        assert factors["weight_kg"] == 1.0


# ============================================================================
# POLYMORPHISM TESTS
# ============================================================================

class TestPolymorphism:
    """Tests for polymorphic behavior of components."""
    
    def test_simple_and_composite_share_interface(self):
        """Both SimpleComponent and CompositeProduct extend ProductComponent."""
        simple = SimpleComponent(name="S", material="m", weight_kg=1.0, environmental_impact=1.0)
        composite = CompositeProduct(name="C")
        
        # Both should have get_impact_factors method
        assert hasattr(simple, "get_impact_factors")
        assert hasattr(composite, "get_impact_factors")
        
        # Both should return dict from get_impact_factors
        assert isinstance(simple.get_impact_factors(), dict)
        assert isinstance(composite.get_impact_factors(), dict)
    
    def test_uniform_treatment(self):
        """Components can be treated uniformly regardless of type."""
        simple = SimpleComponent(
            name="Simple", material="m", weight_kg=1.0, environmental_impact=1.0,
            energy_consumption_mj=10.0
        )
        composite = CompositeProduct(name="Composite")
        child = SimpleComponent(
            name="Child", material="m", weight_kg=2.0, environmental_impact=2.0,
            energy_consumption_mj=20.0
        )
        composite.add(child)
        
        # Can iterate over mixed types
        components = [simple, composite]
        total_energy = sum(c.get_impact_factors()["energy"] for c in components)
        
        assert total_energy == 30.0  # 10 + 20
