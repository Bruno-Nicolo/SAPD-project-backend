from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model for storing authenticated users."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    products = relationship("Product", back_populates="owner", cascade="all, delete-orphan")


class Product(Base):
    """Product model for storing fashion products."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    average_score = Column(Float, nullable=True)  # Calculated average of standard strategies

    # Relationships
    owner = relationship("User", back_populates="products")
    components = relationship("Component", back_populates="product", cascade="all, delete-orphan")


class Component(Base):
    """Component model for product sub-components."""
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String, nullable=False)
    material = Column(String, nullable=False)
    weight_kg = Column(Float, nullable=False)
    environmental_impact = Column(Float, nullable=False)  # Calculated from material

    # Detailed attributes for exact scoring
    energy_consumption_mj = Column(Float, default=0.0)
    water_usage_liters = Column(Float, default=0.0)
    waste_generation_kg = Column(Float, default=0.0)
    recyclability_score = Column(Float, default=0.0)
    recycled_content_percentage = Column(Float, default=0.0)

    # Relationships
    product = relationship("Product", back_populates="components")
