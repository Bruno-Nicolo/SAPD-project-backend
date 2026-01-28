"""
Unit tests for the Visitor Pattern - PDF Report Generation.

Tests cover:
- PdfReportVisitor: collecting data from product structure
- Traversal of composite product hierarchy
- Report generation from collected data
"""
import pytest
from app.core.patterns.composite import SimpleComponent, CompositeProduct
from app.core.patterns.visitor import ProductVisitor, PdfReportVisitor


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def simple_component():
    """Create a simple component for testing."""
    return SimpleComponent(
        name="Cotton Fabric",
        material="organic_cotton",
        weight_kg=0.25,
        environmental_impact=4.0,
        energy_consumption_mj=20.0,
        water_usage_liters=100.0,
        waste_generation_kg=0.02,
        recyclability_score=0.7,
        recycled_content_percentage=0.3
    )


@pytest.fixture
def composite_product():
    """Create a composite product with multiple components."""
    product = CompositeProduct(name="Eco T-Shirt")
    
    fabric = SimpleComponent(
        name="Main Fabric",
        material="organic_cotton",
        weight_kg=0.2,
        environmental_impact=3.5,
        energy_consumption_mj=18.0,
        water_usage_liters=80.0,
        waste_generation_kg=0.015,
        recyclability_score=0.75,
        recycled_content_percentage=0.4
    )
    
    buttons = SimpleComponent(
        name="Buttons",
        material="recycled_plastic",
        weight_kg=0.01,
        environmental_impact=0.5,
        energy_consumption_mj=2.0,
        water_usage_liters=5.0,
        waste_generation_kg=0.001,
        recyclability_score=0.9,
        recycled_content_percentage=1.0
    )
    
    product.add(fabric)
    product.add(buttons)
    return product


@pytest.fixture
def multi_product_structure():
    """Create multiple products for comprehensive testing."""
    product1 = CompositeProduct(name="T-Shirt")
    product1.add(SimpleComponent(
        name="Fabric", material="cotton", weight_kg=0.2,
        environmental_impact=4.0, energy_consumption_mj=15.0,
        water_usage_liters=100.0, waste_generation_kg=0.02,
        recyclability_score=0.6, recycled_content_percentage=0.2
    ))
    
    product2 = CompositeProduct(name="Jeans")
    product2.add(SimpleComponent(
        name="Denim", material="cotton", weight_kg=0.5,
        environmental_impact=6.0, energy_consumption_mj=30.0,
        water_usage_liters=200.0, waste_generation_kg=0.05,
        recyclability_score=0.5, recycled_content_percentage=0.1
    ))
    product2.add(SimpleComponent(
        name="Zipper", material="metal", weight_kg=0.02,
        environmental_impact=0.8, energy_consumption_mj=5.0,
        water_usage_liters=3.0, waste_generation_kg=0.002,
        recyclability_score=0.95, recycled_content_percentage=0.5
    ))
    
    return [product1, product2]


# ============================================================================
# PDF REPORT VISITOR TESTS
# ============================================================================

class TestPdfReportVisitor:
    """Tests for PdfReportVisitor."""
    
    def test_initial_state_empty(self):
        """Visitor should start with no collected products."""
        visitor = PdfReportVisitor()
        assert visitor.products == []
        assert visitor.get_products_data() == []
    
    def test_visit_simple_component_without_product(self, simple_component):
        """Visiting component without product context should be safe."""
        visitor = PdfReportVisitor()
        # Should not raise, just do nothing
        visitor.visit_simple_component(simple_component)
        assert visitor.products == []
    
    def test_visit_composite_product(self, composite_product):
        """Visiting composite product should initialize product data."""
        visitor = PdfReportVisitor()
        visitor.visit_composite_product(composite_product)
        
        assert len(visitor.products) == 1
        assert visitor.products[0]["name"] == "Eco T-Shirt"
        assert "components" in visitor.products[0]
        assert "impact_factors" in visitor.products[0]
    
    def test_accept_traverses_structure(self, composite_product):
        """accept() should traverse entire product structure."""
        visitor = PdfReportVisitor()
        composite_product.accept(visitor)
        
        products_data = visitor.get_products_data()
        assert len(products_data) == 1
        
        product = products_data[0]
        assert product["name"] == "Eco T-Shirt"
        assert len(product["components"]) == 2
        
        # Verify component data
        component_names = [c["name"] for c in product["components"]]
        assert "Main Fabric" in component_names
        assert "Buttons" in component_names
    
    def test_component_data_complete(self, composite_product):
        """Component data should contain all fields."""
        visitor = PdfReportVisitor()
        composite_product.accept(visitor)
        
        component = visitor.products[0]["components"][0]
        
        # All expected fields should be present
        assert "name" in component
        assert "material" in component
        assert "weight_kg" in component
        assert "environmental_impact" in component
        assert "energy_consumption_mj" in component
        assert "water_usage_liters" in component
        assert "waste_generation_kg" in component
        assert "recyclability_score" in component
        assert "recycled_content_percentage" in component
    
    def test_impact_factors_included(self, composite_product):
        """Product impact factors should be included in data."""
        visitor = PdfReportVisitor()
        composite_product.accept(visitor)
        
        impact_factors = visitor.products[0]["impact_factors"]
        
        assert "energy" in impact_factors
        assert "water" in impact_factors
        assert "waste" in impact_factors
        assert "weight_kg" in impact_factors
    
    def test_multiple_products(self, multi_product_structure):
        """Visitor can collect data from multiple products."""
        visitor = PdfReportVisitor()
        
        for product in multi_product_structure:
            product.accept(visitor)
        
        products_data = visitor.get_products_data()
        assert len(products_data) == 2
        
        product_names = [p["name"] for p in products_data]
        assert "T-Shirt" in product_names
        assert "Jeans" in product_names


# ============================================================================
# TEXT REPORT GENERATION TESTS
# ============================================================================

class TestTextReportGeneration:
    """Tests for text-based report generation."""
    
    def test_get_report_empty(self):
        """Empty visitor should return empty report."""
        visitor = PdfReportVisitor()
        report = visitor.get_report()
        assert report == ""
    
    def test_get_report_single_product(self, composite_product):
        """Report should contain product information."""
        visitor = PdfReportVisitor()
        composite_product.accept(visitor)
        
        report = visitor.get_report()
        
        assert "Product Report: Eco T-Shirt" in report
        assert "Main Fabric" in report
        assert "Buttons" in report
        assert "organic_cotton" in report
    
    def test_get_report_multiple_products(self, multi_product_structure):
        """Report should contain all products."""
        visitor = PdfReportVisitor()
        for product in multi_product_structure:
            product.accept(visitor)
        
        report = visitor.get_report()
        
        assert "T-Shirt" in report
        assert "Jeans" in report
        assert "Fabric" in report
        assert "Denim" in report
        assert "Zipper" in report
    
    def test_report_format(self, composite_product):
        """Report should have consistent format."""
        visitor = PdfReportVisitor()
        composite_product.accept(visitor)
        
        report = visitor.get_report()
        lines = report.split("\n")
        
        # Should have header line
        assert any("Product Report:" in line for line in lines)
        # Should have separator
        assert any("-" * 20 in line for line in lines)
        # Should have component lines with proper markers
        assert any("- Component:" in line for line in lines)


# ============================================================================
# NESTED STRUCTURE TESTS
# ============================================================================

class TestNestedStructures:
    """Tests for nested product structures."""
    
    def test_nested_composite(self):
        """Visitor should handle nested composite products."""
        outer = CompositeProduct(name="Complete Outfit")
        
        shirt = CompositeProduct(name="Shirt")
        shirt.add(SimpleComponent(
            name="Shirt Fabric", material="cotton", weight_kg=0.2,
            environmental_impact=3.0
        ))
        
        pants = CompositeProduct(name="Pants")
        pants.add(SimpleComponent(
            name="Pants Fabric", material="denim", weight_kg=0.5,
            environmental_impact=5.0
        ))
        
        outer.add(shirt)
        outer.add(pants)
        
        visitor = PdfReportVisitor()
        outer.accept(visitor)
        
        # Should collect data from nested structure
        assert len(visitor.products) >= 1


# ============================================================================
# CUSTOM VISITOR TESTS
# ============================================================================

class TestCustomVisitor:
    """Tests for custom visitor implementations."""
    
    def test_custom_visitor(self, composite_product):
        """Custom visitors can be created."""
        
        class CountingVisitor(ProductVisitor):
            def __init__(self):
                self.component_count = 0
                self.product_count = 0
            
            def visit_simple_component(self, component):
                self.component_count += 1
            
            def visit_composite_product(self, product):
                self.product_count += 1
        
        visitor = CountingVisitor()
        composite_product.accept(visitor)
        
        assert visitor.product_count == 1
        assert visitor.component_count == 2  # Two components in fixture
    
    def test_visitor_with_filtering(self, composite_product):
        """Custom visitor can filter components."""
        
        class HeavyComponentVisitor(ProductVisitor):
            def __init__(self, min_weight: float):
                self.min_weight = min_weight
                self.heavy_components = []
            
            def visit_simple_component(self, component):
                if component.weight_kg >= self.min_weight:
                    self.heavy_components.append(component.name)
            
            def visit_composite_product(self, product):
                pass
        
        visitor = HeavyComponentVisitor(min_weight=0.1)
        composite_product.accept(visitor)
        
        # Only "Main Fabric" (0.2 kg) should be heavy enough
        assert "Main Fabric" in visitor.heavy_components
        assert "Buttons" not in visitor.heavy_components  # 0.01 kg
