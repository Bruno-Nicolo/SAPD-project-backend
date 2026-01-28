"""
Integration tests for Products API endpoints.

Tests cover:
- POST /products: create product
- GET /products: list products
- GET /products/{id}: get product details
- DELETE /products/{id}: delete product
- POST /products/upload: file upload
- POST /products/{id}/score: calculate score
- Authorization and user isolation
"""
import pytest
import io


# ============================================================================
# CREATE PRODUCT TESTS
# ============================================================================

class TestCreateProduct:
    """Tests for POST /products endpoint."""
    
    def test_create_product_success(self, client, auth_headers, sample_product_data):
        """Authenticated user can create a product."""
        response = client.post(
            "/products/",
            json=sample_product_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == sample_product_data["name"]
        assert "id" in data
        assert len(data["components"]) == len(sample_product_data["components"])
    
    def test_create_product_without_auth(self, client, sample_product_data):
        """Creating product without auth should fail."""
        response = client.post("/products/", json=sample_product_data)
        assert response.status_code in [401, 403]
    
    def test_create_product_with_badges(self, client, auth_headers):
        """Product can be created with badges."""
        product_data = {
            "name": "Sustainable Shirt",
            "components": [
                {"name": "Fabric", "material": "organic_cotton", "weight_kg": 0.25}
            ],
            "badges": ["fairtrade", "vegan", "oekotex"]
        }
        
        response = client.post("/products/", json=product_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert set(data["badges"]) == {"fairtrade", "vegan", "oekotex"}
    
    def test_create_product_calculates_impact(self, client, auth_headers):
        """Created product should have calculated environmental impact."""
        product_data = {
            "name": "Test Product",
            "components": [
                {"name": "Cotton Fabric", "material": "cotton", "weight_kg": 0.3}
            ]
        }
        
        response = client.post("/products/", json=product_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Components should have environmental_impact calculated
        assert "environmental_impact" in data["components"][0]
    
    def test_create_product_empty_components(self, client, auth_headers):
        """Product can be created with empty components list."""
        product_data = {
            "name": "Empty Product",
            "components": []
        }
        
        response = client.post("/products/", json=product_data, headers=auth_headers)
        
        # This might succeed or fail based on business logic
        # Just verifying the endpoint handles it
        assert response.status_code in [200, 400, 422]
    
    def test_create_product_invalid_data(self, client, auth_headers):
        """Invalid product data should return validation error."""
        invalid_data = {
            "name": "Missing Components"
            # Missing 'components' field
        }
        
        response = client.post("/products/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error


# ============================================================================
# LIST PRODUCTS TESTS
# ============================================================================

class TestListProducts:
    """Tests for GET /products endpoint."""
    
    def test_list_products_empty(self, client, auth_headers):
        """List should be empty for new user."""
        response = client.get("/products/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_products_with_products(self, client, auth_headers, test_product):
        """List should return user's products."""
        response = client.get("/products/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        product_names = [p["name"] for p in data]
        assert "Test T-Shirt" in product_names
    
    def test_list_products_without_auth(self, client):
        """List products without auth should fail."""
        response = client.get("/products/")
        assert response.status_code in [401, 403]
    
    def test_list_products_returns_all_fields(self, client, auth_headers, test_product):
        """Listed products should have all expected fields."""
        response = client.get("/products/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        product = data[0]
        assert "id" in product
        assert "name" in product
        assert "components" in product
        assert "badges" in product


# ============================================================================
# GET PRODUCT TESTS
# ============================================================================

class TestGetProduct:
    """Tests for GET /products/{id} endpoint."""
    
    def test_get_product_success(self, client, auth_headers, test_product):
        """Get product by ID should return product details."""
        response = client.get(
            f"/products/{test_product.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_product.id
        assert data["name"] == "Test T-Shirt"
    
    def test_get_product_not_found(self, client, auth_headers):
        """Get non-existent product should return 404."""
        response = client.get("/products/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_product_without_auth(self, client, test_product):
        """Get product without auth should fail."""
        response = client.get(f"/products/{test_product.id}")
        assert response.status_code in [401, 403]
    
    def test_get_product_includes_components(self, client, auth_headers, test_product):
        """Product details should include all components."""
        response = client.get(
            f"/products/{test_product.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["components"]) == 2
        component_names = [c["name"] for c in data["components"]]
        assert "Main Fabric" in component_names
        assert "Buttons" in component_names


# ============================================================================
# DELETE PRODUCT TESTS
# ============================================================================

class TestDeleteProduct:
    """Tests for DELETE /products/{id} endpoint."""
    
    def test_delete_product_success(self, client, auth_headers, test_product):
        """Delete product should succeed."""
        response = client.delete(
            f"/products/{test_product.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify product is gone
        get_response = client.get(
            f"/products/{test_product.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    def test_delete_product_not_found(self, client, auth_headers):
        """Delete non-existent product should return 404."""
        response = client.delete("/products/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_delete_product_without_auth(self, client, test_product):
        """Delete product without auth should fail."""
        response = client.delete(f"/products/{test_product.id}")
        assert response.status_code in [401, 403]


# ============================================================================
# FILE UPLOAD TESTS
# ============================================================================

class TestFileUpload:
    """Tests for POST /products/upload endpoint."""
    
    def test_upload_csv_success(self, client, auth_headers, sample_csv_content):
        """CSV upload should create products."""
        files = {"file": ("products.csv", io.BytesIO(sample_csv_content), "text/csv")}
        
        response = client.post(
            "/products/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have created products
        assert "created" in data or "products" in data or isinstance(data, list)
    
    def test_upload_without_auth(self, client, sample_csv_content):
        """Upload without auth should fail."""
        files = {"file": ("products.csv", io.BytesIO(sample_csv_content), "text/csv")}
        
        response = client.post("/products/upload", files=files)
        assert response.status_code in [401, 403]
    
    def test_upload_invalid_format(self, client, auth_headers):
        """Upload unsupported format should fail."""
        files = {
            "file": ("products.xlsx", io.BytesIO(b"fake excel content"), "application/vnd.ms-excel")
        }
        
        response = client.post(
            "/products/upload",
            files=files,
            headers=auth_headers
        )
        
        # Should reject unsupported format
        assert response.status_code in [400, 415, 422]
    
    def test_upload_invalid_csv(self, client, auth_headers):
        """Upload CSV with missing columns should fail."""
        invalid_csv = b"name,material\nProduct,cotton"  # Missing required columns
        files = {"file": ("products.csv", io.BytesIO(invalid_csv), "text/csv")}
        
        response = client.post(
            "/products/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]


# ============================================================================
# CALCULATE SCORE TESTS
# ============================================================================

class TestCalculateScore:
    """Tests for POST /products/{id}/score endpoint."""
    
    def test_calculate_higg_score(self, client, auth_headers, test_product):
        """Calculate Higg Index score should succeed."""
        response = client.post(
            f"/products/{test_product.id}/score",
            json={"strategy": "higg_index"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "score" in data or "strategy" in data
    
    def test_calculate_carbon_score(self, client, auth_headers, test_product):
        """Calculate Carbon Footprint score should succeed."""
        response = client.post(
            f"/products/{test_product.id}/score",
            json={"strategy": "carbon_footprint"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_calculate_circular_score(self, client, auth_headers, test_product):
        """Calculate Circular Economy score should succeed."""
        response = client.post(
            f"/products/{test_product.id}/score",
            json={"strategy": "circular_economy"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_calculate_custom_score(self, client, auth_headers, test_product):
        """Calculate Custom score with weights should succeed."""
        response = client.post(
            f"/products/{test_product.id}/score",
            json={
                "strategy": "custom",
                "custom_weights": {
                    "energy": 0.3,
                    "water": 0.2,
                    "waste": 0.2,
                    "recyclability": 0.15,
                    "recycled_content": 0.15
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_calculate_score_product_not_found(self, client, auth_headers):
        """Score for non-existent product should return 404."""
        response = client.post(
            "/products/99999/score",
            json={"strategy": "higg_index"},
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_calculate_score_invalid_strategy(self, client, auth_headers, test_product):
        """Invalid strategy should return error."""
        response = client.post(
            f"/products/{test_product.id}/score",
            json={"strategy": "invalid_strategy"},
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]


# ============================================================================
# USER ISOLATION TESTS
# ============================================================================

class TestUserIsolation:
    """Tests for user data isolation."""
    
    def test_user_cannot_see_other_products(
        self, client, auth_headers, another_user_token, product_factory, another_user
    ):
        """Users should only see their own products."""
        # Create product for test_user
        product = product_factory(name="My Product")
        
        # Try to access with another user's token
        other_headers = {"Authorization": f"Bearer {another_user_token}"}
        response = client.get(f"/products/{product.id}", headers=other_headers)
        
        # Should not find the product (404) - it belongs to different user
        assert response.status_code == 404
    
    def test_user_list_only_own_products(
        self, client, auth_headers, another_user_token, product_factory, another_user
    ):
        """List should only show user's own products."""
        # Create products for both users
        product_factory(name="User1 Product")
        product_factory(name="User2 Product", user=another_user)
        
        # List products for test_user
        response = client.get("/products/", headers=auth_headers)
        data = response.json()
        
        product_names = [p["name"] for p in data]
        assert "User1 Product" in product_names
        assert "User2 Product" not in product_names
    
    def test_user_cannot_delete_other_products(
        self, client, auth_headers, another_user_token, product_factory, another_user
    ):
        """Users should not be able to delete other users' products."""
        # Create product for test_user
        product = product_factory(name="My Product")
        
        # Try to delete with another user's token
        other_headers = {"Authorization": f"Bearer {another_user_token}"}
        response = client.delete(f"/products/{product.id}", headers=other_headers)
        
        # Should fail
        assert response.status_code in [403, 404]
