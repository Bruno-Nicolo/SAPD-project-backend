"""
Unit tests for the Decorator Pattern - Product Badges.

Tests cover:
- FairTradeBadge: -5 score bonus
- VeganBadge: -3 score bonus
- OekoTexBadge: -4 score bonus
- NonCompliantBadge: +10 score penalty
- Stacking multiple decorators
"""
import pytest
from app.core.patterns.composite import SimpleComponent, CompositeProduct
from app.core.patterns.decorator import (
    ProductDecorator,
    FairTradeBadge,
    VeganBadge,
    OekoTexBadge,
    NonCompliantBadge,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def base_component():
    """Create a base component for decoration."""
    return SimpleComponent(
        name="Basic Shirt",
        material="cotton",
        weight_kg=0.3,
        environmental_impact=6.0,
        energy_consumption_mj=25.0,
        water_usage_liters=120.0,
        waste_generation_kg=0.05,
        recyclability_score=0.6,
        recycled_content_percentage=0.2
    )


@pytest.fixture
def base_product(base_component):
    """Create a base product containing components."""
    product = CompositeProduct(name="T-Shirt Product")
    product.add(base_component)
    return product


# ============================================================================
# FAIR TRADE BADGE TESTS
# ============================================================================

class TestFairTradeBadge:
    """Tests for FairTradeBadge decorator."""
    
    def test_score_modifier(self, base_component):
        """FairTradeBadge should provide -5 score modifier (bonus)."""
        decorated = FairTradeBadge(base_component)
        assert decorated.get_score_modifier() == -5.0
    
    def test_preserves_component_properties(self, base_component):
        """Decorated component should preserve original properties."""
        decorated = FairTradeBadge(base_component)
        assert decorated.name == base_component.name
        assert decorated.material == base_component.material
        assert decorated.weight_kg == base_component.weight_kg
    
    def test_delegates_impact_factors(self, base_component):
        """Decorated component should delegate get_impact_factors."""
        decorated = FairTradeBadge(base_component)
        original_factors = base_component.get_impact_factors()
        decorated_factors = decorated.get_impact_factors()
        
        assert original_factors == decorated_factors
    
    def test_works_with_product(self, base_product):
        """Badge can be applied to composite products."""
        decorated = FairTradeBadge(base_product)
        assert decorated.get_score_modifier() == -5.0


# ============================================================================
# VEGAN BADGE TESTS
# ============================================================================

class TestVeganBadge:
    """Tests for VeganBadge decorator."""
    
    def test_score_modifier(self, base_component):
        """VeganBadge should provide -3 score modifier (bonus)."""
        decorated = VeganBadge(base_component)
        assert decorated.get_score_modifier() == -3.0
    
    def test_preserves_impact_factors(self, base_component):
        """VeganBadge should preserve original impact factors."""
        decorated = VeganBadge(base_component)
        assert decorated.get_impact_factors() == base_component.get_impact_factors()


# ============================================================================
# OEKO-TEX BADGE TESTS
# ============================================================================

class TestOekoTexBadge:
    """Tests for OekoTexBadge decorator."""
    
    def test_score_modifier(self, base_component):
        """OekoTexBadge should provide -4 score modifier (bonus)."""
        decorated = OekoTexBadge(base_component)
        assert decorated.get_score_modifier() == -4.0
    
    def test_preserves_properties(self, base_component):
        """OekoTexBadge should preserve component properties."""
        decorated = OekoTexBadge(base_component)
        assert decorated.name == base_component.name


# ============================================================================
# NON-COMPLIANT BADGE TESTS
# ============================================================================

class TestNonCompliantBadge:
    """Tests for NonCompliantBadge decorator."""
    
    def test_score_modifier(self, base_component):
        """NonCompliantBadge should provide +10 score modifier (penalty)."""
        decorated = NonCompliantBadge(base_component)
        assert decorated.get_score_modifier() == 10.0
    
    def test_penalty_is_positive(self, base_component):
        """Penalty should be positive (increases environmental score = worse)."""
        decorated = NonCompliantBadge(base_component)
        assert decorated.get_score_modifier() > 0


# ============================================================================
# DECORATOR STACKING TESTS
# ============================================================================

class TestDecoratorStacking:
    """Tests for stacking multiple decorators."""
    
    def test_two_decorators(self, base_component):
        """Two decorators can be stacked."""
        # Apply FairTrade then Vegan
        decorated = VeganBadge(FairTradeBadge(base_component))
        
        # Outer decorator accessible
        assert decorated.get_score_modifier() == -3.0
        
        # Inner decorator still works
        inner = decorated._wrapped
        assert inner.get_score_modifier() == -5.0
    
    def test_three_decorators(self, base_component):
        """Three decorators can be stacked."""
        decorated = OekoTexBadge(VeganBadge(FairTradeBadge(base_component)))
        
        assert decorated.get_score_modifier() == -4.0
    
    def test_calculate_total_modifier(self, base_component):
        """Total modifier from all stacked decorators can be calculated."""
        decorated = OekoTexBadge(VeganBadge(FairTradeBadge(base_component)))
        
        total_modifier = 0.0
        current = decorated
        
        # Walk the decorator chain
        while isinstance(current, ProductDecorator):
            total_modifier += current.get_score_modifier()
            current = current._wrapped
        
        # -4 (OekoTex) + -3 (Vegan) + -5 (FairTrade) = -12
        assert total_modifier == -12.0
    
    def test_opposing_badges(self, base_component):
        """Positive and negative badges can coexist."""
        # Apply both bonuses and penalties
        decorated = NonCompliantBadge(FairTradeBadge(base_component))
        
        # Can still get individual modifiers
        assert decorated.get_score_modifier() == 10.0  # NonCompliant (penalty)
        assert decorated._wrapped.get_score_modifier() == -5.0  # FairTrade (bonus)
    
    def test_stacked_impact_factors_unchanged(self, base_component):
        """Stacking decorators should not change impact factors."""
        original_factors = base_component.get_impact_factors()
        
        decorated = OekoTexBadge(VeganBadge(FairTradeBadge(base_component)))
        decorated_factors = decorated.get_impact_factors()
        
        assert original_factors == decorated_factors


# ============================================================================
# VISITOR PATTERN INTEGRATION
# ============================================================================

class TestDecoratorVisitor:
    """Tests for decorator integration with visitor pattern."""
    
    def test_accept_delegates_to_wrapped(self, base_component):
        """accept() should delegate to wrapped component."""
        decorated = FairTradeBadge(base_component)
        
        # Create a simple visitor that tracks visits
        class TrackingVisitor:
            def __init__(self):
                self.visited = []
            
            def visit_simple_component(self, component):
                self.visited.append(component.name)
            
            def visit_composite_product(self, product):
                self.visited.append(product.name)
        
        visitor = TrackingVisitor()
        decorated.accept(visitor)
        
        # Should have visited the wrapped component
        assert "Basic Shirt" in visitor.visited
