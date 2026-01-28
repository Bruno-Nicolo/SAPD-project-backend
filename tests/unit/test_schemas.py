"""
Unit tests for Pydantic Schemas - Input Validation.

Tests cover:
- ProductCreate: product creation input validation
- ComponentCreate: component creation input validation
- ScoringRequest: scoring strategy validation
- Data rejection for invalid inputs
"""
import pytest
from pydantic import ValidationError

from app.models.schemas import (
    ComponentCreate,
    ComponentResponse,
    ProductCreate,
    ProductResponse,
    ScoringRequest,
    WeightUpdate,
    HealthResponse,
    ScoreResponse,
)


# ============================================================================
# COMPONENT CREATE TESTS
# ============================================================================

class TestComponentCreate:
    """Tests for ComponentCreate schema."""
    
    def test_valid_minimal_component(self):
        """Component with only required fields should be valid."""
        component = ComponentCreate(
            name="Cotton Fabric",
            material="cotton",
            weight_kg=0.25
        )
        
        assert component.name == "Cotton Fabric"
        assert component.material == "cotton"
        assert component.weight_kg == 0.25
    
    def test_valid_full_component(self):
        """Component with all fields should be valid."""
        component = ComponentCreate(
            name="Full Component",
            material="organic_cotton",
            weight_kg=0.5,
            energy_consumption_mj=25.0,
            water_usage_liters=100.0,
            waste_generation_kg=0.05,
            recyclability_score=0.8,
            recycled_content_percentage=0.3
        )
        
        assert component.energy_consumption_mj == 25.0
        assert component.recyclability_score == 0.8
    
    def test_default_values(self):
        """Optional fields should have default values."""
        component = ComponentCreate(
            name="Minimal",
            material="test",
            weight_kg=0.1
        )
        
        assert component.energy_consumption_mj == 0.0
        assert component.water_usage_liters == 0.0
        assert component.waste_generation_kg == 0.0
        assert component.recyclability_score == 0.0
        assert component.recycled_content_percentage == 0.0
    
    def test_missing_required_name(self):
        """Missing name should raise ValidationError."""
        with pytest.raises(ValidationError):
            ComponentCreate(
                material="cotton",
                weight_kg=0.25
            )
    
    def test_missing_required_material(self):
        """Missing material should raise ValidationError."""
        with pytest.raises(ValidationError):
            ComponentCreate(
                name="Test",
                weight_kg=0.25
            )
    
    def test_missing_required_weight(self):
        """Missing weight should raise ValidationError."""
        with pytest.raises(ValidationError):
            ComponentCreate(
                name="Test",
                material="cotton"
            )
    
    def test_invalid_weight_type(self):
        """Non-numeric weight should raise ValidationError."""
        with pytest.raises(ValidationError):
            ComponentCreate(
                name="Test",
                material="cotton",
                weight_kg="not_a_number"
            )
    
    def test_negative_weight_allowed(self):
        """Negative weight is allowed by schema (validation at API level)."""
        # Schema doesn't enforce positive values - that's business logic
        component = ComponentCreate(
            name="Test",
            material="cotton",
            weight_kg=-0.1
        )
        assert component.weight_kg == -0.1


# ============================================================================
# COMPONENT RESPONSE TESTS
# ============================================================================

class TestComponentResponse:
    """Tests for ComponentResponse schema."""
    
    def test_valid_response(self):
        """ComponentResponse should include all fields."""
        response = ComponentResponse(
            name="Fabric",
            material="cotton",
            weight_kg=0.25,
            environmental_impact=4.0,
            energy_consumption_mj=20.0,
            water_usage_liters=100.0,
            waste_generation_kg=0.02,
            recyclability_score=0.7,
            recycled_content_percentage=0.3
        )
        
        assert response.environmental_impact == 4.0
    
    def test_environmental_impact_required(self):
        """environmental_impact is required in response."""
        with pytest.raises(ValidationError):
            ComponentResponse(
                name="Fabric",
                material="cotton",
                weight_kg=0.25,
                energy_consumption_mj=20.0,
                water_usage_liters=100.0,
                waste_generation_kg=0.02,
                recyclability_score=0.7,
                recycled_content_percentage=0.3
                # Missing environmental_impact
            )


# ============================================================================
# PRODUCT CREATE TESTS
# ============================================================================

class TestProductCreate:
    """Tests for ProductCreate schema."""
    
    def test_valid_product_minimal(self):
        """Product with name and components should be valid."""
        product = ProductCreate(
            name="T-Shirt",
            components=[
                ComponentCreate(
                    name="Fabric",
                    material="cotton",
                    weight_kg=0.25
                )
            ]
        )
        
        assert product.name == "T-Shirt"
        assert len(product.components) == 1
    
    def test_valid_product_with_badges(self):
        """Product with badges should be valid."""
        product = ProductCreate(
            name="Eco Shirt",
            components=[
                ComponentCreate(name="Fabric", material="cotton", weight_kg=0.25)
            ],
            badges=["fairtrade", "vegan"]
        )
        
        assert product.badges == ["fairtrade", "vegan"]
    
    def test_default_empty_badges(self):
        """Badges should default to empty list."""
        product = ProductCreate(
            name="Product",
            components=[
                ComponentCreate(name="C", material="m", weight_kg=0.1)
            ]
        )
        
        assert product.badges == []
    
    def test_missing_name(self):
        """Missing name should raise ValidationError."""
        with pytest.raises(ValidationError):
            ProductCreate(
                components=[
                    ComponentCreate(name="C", material="m", weight_kg=0.1)
                ]
            )
    
    def test_missing_components(self):
        """Missing components should raise ValidationError."""
        with pytest.raises(ValidationError):
            ProductCreate(name="Product")
    
    def test_empty_components_allowed(self):
        """Empty components list is allowed by schema."""
        product = ProductCreate(
            name="Empty Product",
            components=[]
        )
        assert product.components == []
    
    def test_multiple_components(self):
        """Product can have multiple components."""
        product = ProductCreate(
            name="Complex Product",
            components=[
                ComponentCreate(name="C1", material="m1", weight_kg=0.1),
                ComponentCreate(name="C2", material="m2", weight_kg=0.2),
                ComponentCreate(name="C3", material="m3", weight_kg=0.3),
            ]
        )
        
        assert len(product.components) == 3


# ============================================================================
# PRODUCT RESPONSE TESTS
# ============================================================================

class TestProductResponse:
    """Tests for ProductResponse schema."""
    
    def test_valid_response(self):
        """ProductResponse with all fields should be valid."""
        response = ProductResponse(
            id=1,
            name="T-Shirt",
            average_score=75.5,
            badges=["fairtrade"],
            components=[
                ComponentResponse(
                    name="Fabric",
                    material="cotton",
                    weight_kg=0.25,
                    environmental_impact=4.0,
                    energy_consumption_mj=20.0,
                    water_usage_liters=100.0,
                    waste_generation_kg=0.02,
                    recyclability_score=0.7,
                    recycled_content_percentage=0.3
                )
            ]
        )
        
        assert response.id == 1
        assert response.average_score == 75.5
    
    def test_optional_id(self):
        """id is optional in response."""
        response = ProductResponse(
            name="Product",
            components=[],
            badges=[]
        )
        
        assert response.id is None
    
    def test_optional_average_score(self):
        """average_score is optional in response."""
        response = ProductResponse(
            id=1,
            name="Product",
            components=[],
            badges=[]
        )
        
        assert response.average_score is None


# ============================================================================
# SCORING REQUEST TESTS
# ============================================================================

class TestScoringRequest:
    """Tests for ScoringRequest schema."""
    
    def test_valid_strategy(self):
        """Valid strategy should be accepted."""
        request = ScoringRequest(strategy="higg_index")
        assert request.strategy == "higg_index"
    
    def test_custom_strategy_with_weights(self):
        """Custom strategy can include weights."""
        request = ScoringRequest(
            strategy="custom",
            custom_weights={
                "energy": 0.3,
                "water": 0.2,
                "waste": 0.2,
                "recyclability": 0.15,
                "recycled_content": 0.15
            }
        )
        
        assert request.custom_weights is not None
        assert request.custom_weights["energy"] == 0.3
    
    def test_default_no_custom_weights(self):
        """custom_weights should default to None."""
        request = ScoringRequest(strategy="carbon_footprint")
        assert request.custom_weights is None
    
    def test_missing_strategy(self):
        """Missing strategy should raise ValidationError."""
        with pytest.raises(ValidationError):
            ScoringRequest()


# ============================================================================
# WEIGHT UPDATE TESTS
# ============================================================================

class TestWeightUpdate:
    """Tests for WeightUpdate schema."""
    
    def test_valid_weights(self):
        """Valid weights dictionary should be accepted."""
        update = WeightUpdate(
            weights={
                "material_sustainability": 0.3,
                "carbon_footprint": 0.25
            }
        )
        
        assert update.weights["material_sustainability"] == 0.3
    
    def test_missing_weights(self):
        """Missing weights should raise ValidationError."""
        with pytest.raises(ValidationError):
            WeightUpdate()
    
    def test_empty_weights_allowed(self):
        """Empty weights dictionary is allowed."""
        update = WeightUpdate(weights={})
        assert update.weights == {}


# ============================================================================
# SIMPLE SCHEMAS TESTS
# ============================================================================

class TestSimpleSchemas:
    """Tests for simple response schemas."""
    
    def test_health_response(self):
        """HealthResponse should have status field."""
        response = HealthResponse(status="healthy")
        assert response.status == "healthy"
    
    def test_score_response(self):
        """ScoreResponse should have strategy and score."""
        response = ScoreResponse(strategy="higg_index", score=85.5)
        assert response.strategy == "higg_index"
        assert response.score == 85.5


# ============================================================================
# SERIALIZATION TESTS
# ============================================================================

class TestSerialization:
    """Tests for JSON serialization/deserialization."""
    
    def test_component_to_dict(self):
        """Component should serialize to dict."""
        component = ComponentCreate(
            name="Test",
            material="cotton",
            weight_kg=0.25
        )
        
        data = component.model_dump()
        assert data["name"] == "Test"
        assert data["weight_kg"] == 0.25
    
    def test_product_to_dict(self):
        """Product should serialize nested components."""
        product = ProductCreate(
            name="Product",
            components=[
                ComponentCreate(name="C", material="m", weight_kg=0.1)
            ]
        )
        
        data = product.model_dump()
        assert len(data["components"]) == 1
        assert data["components"][0]["name"] == "C"
    
    def test_from_dict(self):
        """Products can be created from dictionaries."""
        data = {
            "name": "From Dict",
            "components": [
                {"name": "C1", "material": "m1", "weight_kg": 0.1}
            ],
            "badges": ["vegan"]
        }
        
        product = ProductCreate(**data)
        assert product.name == "From Dict"
        assert len(product.components) == 1
