"""
Pytest configuration and shared fixtures for SAPD Backend tests.

This module provides:
- In-memory SQLite database for test isolation
- FastAPI TestClient for API testing
- Mock authenticated user with valid JWT token
- Factory functions for creating test objects
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.core.dependencies import create_access_token
from app.models.db_models import User, Product, Component


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_engine():
    """Create an in-memory SQLite engine for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a database session for testing."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a FastAPI TestClient with overridden database dependency."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_user(test_db) -> User:
    """Create a test user in the database."""
    user = User(
        email="test@example.com",
        name="Test User",
        google_id="google_test_123",
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_token(test_user) -> str:
    """Create a valid JWT token for the test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture(scope="function")
def auth_headers(test_user_token) -> dict:
    """Create authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture(scope="function")
def another_user(test_db) -> User:
    """Create another test user for isolation testing."""
    user = User(
        email="another@example.com",
        name="Another User",
        google_id="google_another_456",
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def another_user_token(another_user) -> str:
    """Create a valid JWT token for the another user."""
    return create_access_token(data={"sub": str(another_user.id)})


# ============================================================================
# PRODUCT FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_product(test_db, test_user) -> Product:
    """Create a test product with components."""
    product = Product(
        name="Test T-Shirt",
        user_id=test_user.id,
        average_score=75.0,
        badges=["fairtrade"],
        created_at=datetime.utcnow()
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    
    # Add components
    component1 = Component(
        product_id=product.id,
        name="Main Fabric",
        material="organic_cotton",
        weight_kg=0.2,
        environmental_impact=0.8,
        energy_consumption_mj=15.0,
        water_usage_liters=100.0,
        waste_generation_kg=0.02,
        recyclability_score=0.7,
        recycled_content_percentage=0.3
    )
    component2 = Component(
        product_id=product.id,
        name="Buttons",
        material="recycled_plastic",
        weight_kg=0.01,
        environmental_impact=0.055,
        energy_consumption_mj=2.0,
        water_usage_liters=5.0,
        waste_generation_kg=0.001,
        recyclability_score=0.9,
        recycled_content_percentage=1.0
    )
    test_db.add_all([component1, component2])
    test_db.commit()
    test_db.refresh(product)
    
    return product


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

@pytest.fixture
def product_factory(test_db, test_user):
    """Factory fixture to create products with custom attributes."""
    created_products = []
    
    def _create_product(
        name: str = "Factory Product",
        user: User = None,
        average_score: float = None,
        badges: list = None,
        components: list = None
    ) -> Product:
        product = Product(
            name=name,
            user_id=(user or test_user).id,
            average_score=average_score,
            badges=badges or [],
            created_at=datetime.utcnow()
        )
        test_db.add(product)
        test_db.commit()
        test_db.refresh(product)
        
        if components:
            for comp_data in components:
                component = Component(
                    product_id=product.id,
                    name=comp_data.get("name", "Component"),
                    material=comp_data.get("material", "cotton"),
                    weight_kg=comp_data.get("weight_kg", 0.1),
                    environmental_impact=comp_data.get("environmental_impact", 0.5),
                    energy_consumption_mj=comp_data.get("energy_consumption_mj", 10.0),
                    water_usage_liters=comp_data.get("water_usage_liters", 50.0),
                    waste_generation_kg=comp_data.get("waste_generation_kg", 0.01),
                    recyclability_score=comp_data.get("recyclability_score", 0.5),
                    recycled_content_percentage=comp_data.get("recycled_content_percentage", 0.0)
                )
                test_db.add(component)
            test_db.commit()
            test_db.refresh(product)
        
        created_products.append(product)
        return product
    
    yield _create_product


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_product_data() -> dict:
    """Sample product data for API testing."""
    return {
        "name": "Eco Jeans",
        "components": [
            {
                "name": "Denim Fabric",
                "material": "organic_cotton",
                "weight_kg": 0.5,
                "energy_consumption_mj": 25.0,
                "water_usage_liters": 200.0,
                "waste_generation_kg": 0.05,
                "recyclability_score": 0.6,
                "recycled_content_percentage": 0.2
            },
            {
                "name": "Zipper",
                "material": "metal",
                "weight_kg": 0.02,
                "energy_consumption_mj": 5.0,
                "water_usage_liters": 2.0,
                "waste_generation_kg": 0.002,
                "recyclability_score": 0.95,
                "recycled_content_percentage": 0.5
            }
        ],
        "badges": ["vegan"]
    }


@pytest.fixture
def sample_csv_content() -> bytes:
    """Sample CSV content for upload testing."""
    csv_data = """product_name,component_name,material,weight_kg,energy_consumption_mj,water_usage_liters,waste_generation_kg,recyclability_score,recycled_content_percentage
Test Shirt,Cotton Body,organic_cotton,0.25,20.0,150.0,0.03,0.7,0.4
Test Shirt,Buttons,recycled_plastic,0.01,3.0,5.0,0.001,0.9,1.0
Test Pants,Denim,cotton,0.4,30.0,250.0,0.05,0.5,0.1
Test Pants,Zipper,metal,0.02,4.0,3.0,0.002,0.95,0.6"""
    return csv_data.encode('utf-8')
