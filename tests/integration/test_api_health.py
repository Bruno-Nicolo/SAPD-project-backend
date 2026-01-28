"""
Integration tests for Health API endpoint.

Tests cover:
- GET /health: basic health check
"""
import pytest


class TestHealthEndpoint:
    """Integration tests for /health endpoint."""
    
    def test_health_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_response_format(self, client):
        """Health endpoint should return proper JSON format."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_no_auth_required(self, client):
        """Health endpoint should not require authentication."""
        # No auth headers provided
        response = client.get("/health")
        assert response.status_code == 200
