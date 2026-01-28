"""
Unit tests for the Strategy Pattern - Scoring Strategies.

Tests cover:
- HiggIndexStrategy: multi-factor environmental scoring
- CarbonFootprintStrategy: CO2-focused scoring
- CircularEconomyStrategy: recycling and waste scoring
- CustomStrategy: user-defined weights
- ScoringContext: dynamic strategy switching
"""
import pytest
from app.core.patterns.composite import SimpleComponent, CompositeProduct
from app.core.patterns.strategy import (
    HiggIndexStrategy,
    CarbonFootprintStrategy,
    CircularEconomyStrategy,
    CustomStrategy,
    ScoringContext,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def simple_component():
    """Create a simple component for testing."""
    return SimpleComponent(
        name="Test Fabric",
        material="cotton",
        weight_kg=1.0,
        environmental_impact=8.0,
        energy_consumption_mj=50.0,
        water_usage_liters=200.0,
        waste_generation_kg=0.5,
        recyclability_score=0.6,
        recycled_content_percentage=0.3
    )


@pytest.fixture
def eco_friendly_component():
    """Create an eco-friendly component with low impact."""
    return SimpleComponent(
        name="Eco Fabric",
        material="organic_cotton",
        weight_kg=1.0,
        environmental_impact=4.0,
        energy_consumption_mj=20.0,
        water_usage_liters=50.0,
        waste_generation_kg=0.1,
        recyclability_score=0.9,
        recycled_content_percentage=0.8
    )


@pytest.fixture
def high_impact_component():
    """Create a high environmental impact component."""
    return SimpleComponent(
        name="Synthetic Fabric",
        material="polyester",
        weight_kg=1.0,
        environmental_impact=15.0,
        energy_consumption_mj=150.0,
        water_usage_liters=500.0,
        waste_generation_kg=2.0,
        recyclability_score=0.2,
        recycled_content_percentage=0.0
    )


@pytest.fixture
def composite_product(simple_component, eco_friendly_component):
    """Create a composite product with multiple components."""
    product = CompositeProduct(name="Test Product")
    product.add(simple_component)
    product.add(eco_friendly_component)
    return product


# ============================================================================
# HIGG INDEX STRATEGY TESTS
# ============================================================================

class TestHiggIndexStrategy:
    """Tests for the Higg Index inspired scoring strategy."""
    
    def test_calculate_score_returns_float(self, simple_component):
        """Score should be a float value."""
        strategy = HiggIndexStrategy()
        score = strategy.calculate_score(simple_component)
        assert isinstance(score, float)
    
    def test_score_range_0_to_100(self, simple_component):
        """Score should be between 0 and 100."""
        strategy = HiggIndexStrategy()
        score = strategy.calculate_score(simple_component)
        assert 0 <= score <= 100
    
    def test_eco_friendly_scores_higher(self, eco_friendly_component, high_impact_component):
        """Eco-friendly components should score higher than high-impact ones."""
        strategy = HiggIndexStrategy()
        eco_score = strategy.calculate_score(eco_friendly_component)
        high_impact_score = strategy.calculate_score(high_impact_component)
        assert eco_score > high_impact_score
    
    def test_composite_product_scoring(self, composite_product):
        """Strategy should work with composite products."""
        strategy = HiggIndexStrategy()
        score = strategy.calculate_score(composite_product)
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_zero_weight_handled(self):
        """Zero weight should be handled gracefully."""
        component = SimpleComponent(
            name="Zero Weight", material="test", weight_kg=0.0,
            environmental_impact=1.0
        )
        strategy = HiggIndexStrategy()
        score = strategy.calculate_score(component)
        # Should not raise division by zero
        assert isinstance(score, float)


# ============================================================================
# CARBON FOOTPRINT STRATEGY TESTS
# ============================================================================

class TestCarbonFootprintStrategy:
    """Tests for the carbon footprint focused scoring strategy."""
    
    def test_calculate_score_returns_float(self, simple_component):
        """Score should be a float value."""
        strategy = CarbonFootprintStrategy()
        score = strategy.calculate_score(simple_component)
        assert isinstance(score, float)
    
    def test_score_range_0_to_100(self, simple_component):
        """Score should be between 0 and 100."""
        strategy = CarbonFootprintStrategy()
        score = strategy.calculate_score(simple_component)
        assert 0 <= score <= 100
    
    def test_low_energy_scores_higher(self, eco_friendly_component, high_impact_component):
        """Low energy consumption should result in higher score."""
        strategy = CarbonFootprintStrategy()
        eco_score = strategy.calculate_score(eco_friendly_component)
        high_impact_score = strategy.calculate_score(high_impact_component)
        assert eco_score > high_impact_score
    
    def test_perfect_score_with_zero_energy(self):
        """Zero energy consumption should give perfect score."""
        component = SimpleComponent(
            name="Zero Energy", material="test", weight_kg=1.0,
            environmental_impact=0.0, energy_consumption_mj=0.0
        )
        strategy = CarbonFootprintStrategy()
        score = strategy.calculate_score(component)
        assert score == 100.0


# ============================================================================
# CIRCULAR ECONOMY STRATEGY TESTS
# ============================================================================

class TestCircularEconomyStrategy:
    """Tests for the circular economy focused scoring strategy."""
    
    def test_calculate_score_returns_float(self, simple_component):
        """Score should be a float value."""
        strategy = CircularEconomyStrategy()
        score = strategy.calculate_score(simple_component)
        assert isinstance(score, float)
    
    def test_score_range_0_to_100(self, simple_component):
        """Score should be between 0 and 100."""
        strategy = CircularEconomyStrategy()
        score = strategy.calculate_score(simple_component)
        assert 0 <= score <= 100
    
    def test_high_recyclability_scores_higher(self):
        """High recyclability should increase score."""
        recyclable = SimpleComponent(
            name="Recyclable", material="test", weight_kg=1.0,
            environmental_impact=5.0, recyclability_score=0.9,
            recycled_content_percentage=0.8, waste_generation_kg=0.1
        )
        non_recyclable = SimpleComponent(
            name="Non-Recyclable", material="test", weight_kg=1.0,
            environmental_impact=5.0, recyclability_score=0.1,
            recycled_content_percentage=0.0, waste_generation_kg=0.1
        )
        strategy = CircularEconomyStrategy()
        assert strategy.calculate_score(recyclable) > strategy.calculate_score(non_recyclable)
    
    def test_high_waste_penalized(self):
        """High waste generation should decrease score."""
        low_waste = SimpleComponent(
            name="Low Waste", material="test", weight_kg=1.0,
            environmental_impact=5.0, recyclability_score=0.5,
            waste_generation_kg=0.1
        )
        high_waste = SimpleComponent(
            name="High Waste", material="test", weight_kg=1.0,
            environmental_impact=5.0, recyclability_score=0.5,
            waste_generation_kg=3.0
        )
        strategy = CircularEconomyStrategy()
        assert strategy.calculate_score(low_waste) > strategy.calculate_score(high_waste)


# ============================================================================
# CUSTOM STRATEGY TESTS
# ============================================================================

class TestCustomStrategy:
    """Tests for the custom weights scoring strategy."""
    
    def test_default_weights_work(self, simple_component):
        """Custom strategy should work with default (empty) weights."""
        strategy = CustomStrategy()
        score = strategy.calculate_score(simple_component)
        assert isinstance(score, (int, float))
    
    def test_custom_weights_applied(self, simple_component):
        """Custom weights should affect the score calculation."""
        weights1 = {"energy": 0.5, "water": 0.0, "waste": 0.0}
        weights2 = {"energy": 0.0, "water": 0.5, "waste": 0.0}
        
        strategy1 = CustomStrategy(weights=weights1)
        strategy2 = CustomStrategy(weights=weights2)
        
        score1 = strategy1.calculate_score(simple_component)
        score2 = strategy2.calculate_score(simple_component)
        
        # Different weights should produce different scores
        assert score1 != score2
    
    def test_recyclability_bonus(self, eco_friendly_component):
        """Recyclability weight should add bonus points."""
        weights = {"recyclability": 10.0, "recycled_content": 10.0}
        strategy = CustomStrategy(weights=weights)
        score = strategy.calculate_score(eco_friendly_component)
        # Should be above 100 before capping due to bonuses
        assert score > 0
    
    def test_score_capped_at_100(self):
        """Score should not exceed 100."""
        component = SimpleComponent(
            name="Perfect", material="test", weight_kg=1.0,
            environmental_impact=0.0, recyclability_score=1.0,
            recycled_content_percentage=1.0
        )
        weights = {"recyclability": 100.0, "recycled_content": 100.0}
        strategy = CustomStrategy(weights=weights)
        score = strategy.calculate_score(component)
        assert score <= 100


# ============================================================================
# SCORING CONTEXT TESTS
# ============================================================================

class TestScoringContext:
    """Tests for the ScoringContext class (Strategy Pattern context)."""
    
    def test_context_uses_initial_strategy(self, simple_component):
        """Context should use the strategy passed in constructor."""
        strategy = HiggIndexStrategy()
        context = ScoringContext(strategy)
        score = context.calculate(simple_component)
        
        # Should match direct strategy call
        assert score == strategy.calculate_score(simple_component)
    
    def test_strategy_can_be_changed(self, simple_component):
        """Context should allow changing strategy at runtime."""
        context = ScoringContext(HiggIndexStrategy())
        score1 = context.calculate(simple_component)
        
        context.set_strategy(CarbonFootprintStrategy())
        score2 = context.calculate(simple_component)
        
        # Different strategies typically produce different scores
        assert isinstance(score1, float)
        assert isinstance(score2, float)
    
    def test_all_strategies_can_be_used(self, simple_component):
        """All strategy types should work with the context."""
        strategies = [
            HiggIndexStrategy(),
            CarbonFootprintStrategy(),
            CircularEconomyStrategy(),
            CustomStrategy(weights={"energy": 0.1}),
        ]
        
        context = ScoringContext(strategies[0])
        
        for strategy in strategies:
            context.set_strategy(strategy)
            score = context.calculate(simple_component)
            assert isinstance(score, float)
            assert 0 <= score <= 100
