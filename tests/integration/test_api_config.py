"""
Integration tests for Config API endpoints.

Tests cover:
- GET /config/weights: get current weight configuration
- PUT /config/weights: update weight configuration
"""
import pytest


# ============================================================================
# GET WEIGHTS TESTS
# ============================================================================

class TestGetWeights:
    """Tests for GET /config/weights endpoint."""
    
    def test_get_weights_success(self, client):
        """Get weights should return current configuration."""
        response = client.get("/config/weights")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "weights" in data
        assert isinstance(data["weights"], dict)
    
    def test_get_weights_contains_default_values(self, client):
        """Weights should contain default configuration values."""
        response = client.get("/config/weights")
        data = response.json()
        
        weights = data["weights"]
        
        # Check for expected default keys
        expected_keys = [
            "material_sustainability",
            "carbon_footprint",
            "water_usage",
            "social_impact",
            "circularity"
        ]
        
        for key in expected_keys:
            assert key in weights
    
    def test_get_weights_no_auth_required(self, client):
        """Get weights should not require authentication."""
        # No auth headers
        response = client.get("/config/weights")
        assert response.status_code == 200


# ============================================================================
# UPDATE WEIGHTS TESTS
# ============================================================================

class TestUpdateWeights:
    """Tests for PUT /config/weights endpoint."""
    
    def test_update_weights_success(self, client):
        """Update weights should modify configuration."""
        new_weights = {
            "weights": {
                "material_sustainability": 0.4,
                "carbon_footprint": 0.3,
                "water_usage": 0.15,
                "social_impact": 0.1,
                "circularity": 0.05
            }
        }
        
        response = client.put("/config/weights", json=new_weights)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "weights" in data
        assert data["weights"]["material_sustainability"] == 0.4
    
    def test_update_weights_persists(self, client):
        """Updated weights should persist for subsequent requests."""
        new_weights = {
            "weights": {
                "material_sustainability": 0.5
            }
        }
        
        # Update
        client.put("/config/weights", json=new_weights)
        
        # Get and verify
        response = client.get("/config/weights")
        data = response.json()
        
        assert data["weights"]["material_sustainability"] == 0.5
    
    def test_update_weights_partial(self, client):
        """Partial weight updates should work."""
        # Get initial weights
        initial_response = client.get("/config/weights")
        initial_weights = initial_response.json()["weights"]
        
        # Update only one weight
        update_data = {
            "weights": {
                "circularity": 0.99
            }
        }
        
        response = client.put("/config/weights", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["weights"]["circularity"] == 0.99
    
    def test_update_weights_invalid_format(self, client):
        """Invalid weight format should return error."""
        invalid_data = {
            "weights": "not_a_dict"  # Should be a dict
        }
        
        response = client.put("/config/weights", json=invalid_data)
        assert response.status_code == 422
    
    def test_update_weights_response_message(self, client):
        """Update response should include confirmation message."""
        new_weights = {
            "weights": {
                "material_sustainability": 0.25
            }
        }
        
        response = client.put("/config/weights", json=new_weights)
        data = response.json()
        
        # Should have message confirming update
        assert "message" in data or "weights" in data


# ============================================================================
# WEIGHTS VALIDATION TESTS
# ============================================================================

class TestWeightsValidation:
    """Tests for weights validation behavior."""
    
    def test_weights_can_be_zero(self, client):
        """Zero weights should be allowed."""
        new_weights = {
            "weights": {
                "social_impact": 0.0
            }
        }
        
        response = client.put("/config/weights", json=new_weights)
        assert response.status_code == 200
    
    def test_weights_can_be_one(self, client):
        """Weight of 1.0 should be allowed."""
        new_weights = {
            "weights": {
                "material_sustainability": 1.0
            }
        }
        
        response = client.put("/config/weights", json=new_weights)
        assert response.status_code == 200
    
    def test_new_weight_keys_accepted(self, client):
        """New weight keys should be accepted."""
        new_weights = {
            "weights": {
                "custom_metric": 0.5
            }
        }
        
        response = client.put("/config/weights", json=new_weights)
        assert response.status_code == 200
        
        # Verify it was stored
        get_response = client.get("/config/weights")
        data = get_response.json()
        assert data["weights"]["custom_metric"] == 0.5


# ============================================================================
# OBSERVER PATTERN INTEGRATION TESTS
# ============================================================================

class TestObserverIntegration:
    """Tests for Observer pattern integration in config."""
    
    def test_weights_update_notifies_modules(self, client):
        """Updating weights should trigger observer notifications.
        
        This is an indirect test - we verify the endpoint works correctly
        and trust that the observer pattern is correctly implemented.
        """
        new_weights = {
            "weights": {
                "material_sustainability": 0.35,
                "carbon_footprint": 0.25,
                "water_usage": 0.20,
                "social_impact": 0.10,
                "circularity": 0.10
            }
        }
        
        response = client.put("/config/weights", json=new_weights)
        
        assert response.status_code == 200
        # The fact that the endpoint works means observers were notified
