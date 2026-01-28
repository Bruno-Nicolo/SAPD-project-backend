"""
Unit tests for the Adapter Pattern - CSV Product Adapter.

Tests cover:
- CsvProductAdapter: parsing CSV files to ProductData
- Required column validation
- Optional column handling
- Product grouping by name
- Error handling (empty files, missing columns)
"""
import pytest
from app.core.patterns.adapter_facade import (
    ComponentData,
    ProductData,
    ProductFileAdapter,
    CsvProductAdapter,
    get_adapter_for_file,
    get_supported_formats,
    PRODUCT_FILE_ADAPTERS,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def csv_adapter():
    """Create a CSV adapter instance."""
    return CsvProductAdapter()


@pytest.fixture
def valid_csv_minimal():
    """Valid CSV with only required columns."""
    return b"""product_name,component_name,material,weight_kg
T-Shirt,Cotton Fabric,cotton,0.25
T-Shirt,Buttons,plastic,0.01
Jeans,Denim Fabric,cotton,0.50"""


@pytest.fixture
def valid_csv_complete():
    """Valid CSV with all columns."""
    return b"""product_name,component_name,material,weight_kg,energy_consumption_mj,water_usage_liters,waste_generation_kg,recyclability_score,recycled_content_percentage
T-Shirt,Cotton Fabric,cotton,0.25,20.0,100.0,0.02,0.7,0.3
T-Shirt,Buttons,recycled_plastic,0.01,2.0,5.0,0.001,0.9,1.0
Jeans,Denim Fabric,cotton,0.50,30.0,200.0,0.05,0.5,0.1"""


@pytest.fixture
def invalid_csv_missing_columns():
    """CSV missing required columns."""
    return b"""product_name,component_name,material
T-Shirt,Cotton Fabric,cotton"""


@pytest.fixture
def empty_csv():
    """Empty CSV file."""
    return b""


@pytest.fixture
def csv_with_empty_rows():
    """CSV with some empty product names (should be skipped)."""
    return b"""product_name,component_name,material,weight_kg
T-Shirt,Cotton Fabric,cotton,0.25
,Empty Name,unknown,0.0
  ,Whitespace Only,unknown,0.0
T-Shirt,Buttons,plastic,0.01"""


# ============================================================================
# CSV ADAPTER BASIC TESTS
# ============================================================================

class TestCsvProductAdapter:
    """Tests for CsvProductAdapter."""
    
    def test_supported_extension(self, csv_adapter):
        """Adapter should report .csv as supported extension."""
        assert csv_adapter.supported_extension == '.csv'
    
    def test_parse_minimal_csv(self, csv_adapter, valid_csv_minimal):
        """Adapter should parse CSV with only required columns."""
        products = csv_adapter.parse(valid_csv_minimal)
        
        assert len(products) == 2  # T-Shirt and Jeans
        
        product_names = [p.name for p in products]
        assert "T-Shirt" in product_names
        assert "Jeans" in product_names
    
    def test_parse_complete_csv(self, csv_adapter, valid_csv_complete):
        """Adapter should parse CSV with all columns."""
        products = csv_adapter.parse(valid_csv_complete)
        
        assert len(products) == 2
        
        # Find T-Shirt
        tshirt = next(p for p in products if p.name == "T-Shirt")
        assert len(tshirt.components) == 2
        
        # Check first component has all fields
        fabric = next(c for c in tshirt.components if c.name == "Cotton Fabric")
        assert fabric.material == "cotton"
        assert fabric.weight_kg == 0.25
        assert fabric.energy_consumption_mj == 20.0
        assert fabric.water_usage_liters == 100.0
        assert fabric.waste_generation_kg == 0.02
        assert fabric.recyclability_score == 0.7
        assert fabric.recycled_content_percentage == 0.3


# ============================================================================
# PRODUCT GROUPING TESTS
# ============================================================================

class TestProductGrouping:
    """Tests for product grouping functionality."""
    
    def test_components_grouped_by_product(self, csv_adapter, valid_csv_minimal):
        """Components should be grouped under their product."""
        products = csv_adapter.parse(valid_csv_minimal)
        
        tshirt = next(p for p in products if p.name == "T-Shirt")
        assert len(tshirt.components) == 2
        
        component_names = [c.name for c in tshirt.components]
        assert "Cotton Fabric" in component_names
        assert "Buttons" in component_names
    
    def test_single_product_single_component(self, csv_adapter):
        """Single product with single component should work."""
        csv = b"""product_name,component_name,material,weight_kg
Solo,Only Component,cotton,0.5"""
        
        products = csv_adapter.parse(csv)
        assert len(products) == 1
        assert products[0].name == "Solo"
        assert len(products[0].components) == 1
    
    def test_empty_rows_skipped(self, csv_adapter, csv_with_empty_rows):
        """Rows with empty product names should be skipped."""
        products = csv_adapter.parse(csv_with_empty_rows)
        
        # Only T-Shirt should be present
        assert len(products) == 1
        assert products[0].name == "T-Shirt"
        assert len(products[0].components) == 2


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Tests for error handling in CSV parsing."""
    
    def test_missing_required_columns(self, csv_adapter, invalid_csv_missing_columns):
        """Should raise ValueError for missing required columns."""
        with pytest.raises(ValueError) as exc_info:
            csv_adapter.parse(invalid_csv_missing_columns)
        
        assert "missing required columns" in str(exc_info.value).lower()
        assert "weight_kg" in str(exc_info.value)
    
    def test_empty_csv(self, csv_adapter, empty_csv):
        """Should raise ValueError for empty CSV."""
        with pytest.raises(ValueError) as exc_info:
            csv_adapter.parse(empty_csv)
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_invalid_float_handled(self, csv_adapter):
        """Invalid float values should default to 0.0."""
        csv = b"""product_name,component_name,material,weight_kg,energy_consumption_mj
Test,Component,cotton,invalid,also_invalid"""
        
        products = csv_adapter.parse(csv)
        component = products[0].components[0]
        
        # Invalid values should become 0.0
        assert component.weight_kg == 0.0
        assert component.energy_consumption_mj == 0.0
    
    def test_missing_optional_values(self, csv_adapter, valid_csv_minimal):
        """Missing optional columns should default to 0.0."""
        products = csv_adapter.parse(valid_csv_minimal)
        component = products[0].components[0]
        
        # Optional fields should be 0.0
        assert component.energy_consumption_mj == 0.0
        assert component.water_usage_liters == 0.0
        assert component.waste_generation_kg == 0.0
        assert component.recyclability_score == 0.0
        assert component.recycled_content_percentage == 0.0


# ============================================================================
# DATA CLASSES TESTS
# ============================================================================

class TestDataClasses:
    """Tests for ComponentData and ProductData dataclasses."""
    
    def test_component_data_creation(self):
        """ComponentData should be created with proper defaults."""
        component = ComponentData(
            name="Test",
            material="cotton",
            weight_kg=0.5
        )
        
        assert component.name == "Test"
        assert component.material == "cotton"
        assert component.weight_kg == 0.5
        assert component.energy_consumption_mj == 0.0
    
    def test_component_data_full(self):
        """ComponentData should accept all fields."""
        component = ComponentData(
            name="Full",
            material="organic_cotton",
            weight_kg=1.0,
            energy_consumption_mj=25.0,
            water_usage_liters=100.0,
            waste_generation_kg=0.1,
            recyclability_score=0.8,
            recycled_content_percentage=0.5
        )
        
        assert component.recyclability_score == 0.8
    
    def test_product_data_creation(self):
        """ProductData should hold product name and components."""
        components = [
            ComponentData(name="C1", material="m1", weight_kg=0.1),
            ComponentData(name="C2", material="m2", weight_kg=0.2),
        ]
        product = ProductData(name="Test Product", components=components)
        
        assert product.name == "Test Product"
        assert len(product.components) == 2


# ============================================================================
# ADAPTER REGISTRY TESTS
# ============================================================================

class TestAdapterRegistry:
    """Tests for adapter registry functions."""
    
    def test_get_adapter_for_csv(self):
        """get_adapter_for_file should return CSV adapter for .csv files."""
        adapter = get_adapter_for_file("products.csv")
        assert isinstance(adapter, CsvProductAdapter)
    
    def test_get_adapter_for_uppercase_extension(self):
        """get_adapter_for_file should handle uppercase extensions."""
        adapter = get_adapter_for_file("products.CSV")
        assert isinstance(adapter, CsvProductAdapter)
    
    def test_get_adapter_for_unsupported(self):
        """get_adapter_for_file should return None for unsupported formats."""
        adapter = get_adapter_for_file("products.xlsx")
        assert adapter is None
    
    def test_get_adapter_no_extension(self):
        """get_adapter_for_file should return None for files without extension."""
        adapter = get_adapter_for_file("noextension")
        assert adapter is None
    
    def test_get_supported_formats(self):
        """get_supported_formats should return list of extensions."""
        formats = get_supported_formats()
        assert ".csv" in formats
    
    def test_adapter_registry_exists(self):
        """PRODUCT_FILE_ADAPTERS registry should exist and have entries."""
        assert ".csv" in PRODUCT_FILE_ADAPTERS
        assert isinstance(PRODUCT_FILE_ADAPTERS[".csv"], CsvProductAdapter)


# ============================================================================
# ENCODING TESTS
# ============================================================================

class TestEncoding:
    """Tests for character encoding handling."""
    
    def test_utf8_encoding(self, csv_adapter):
        """Adapter should handle UTF-8 encoded content."""
        csv = """product_name,component_name,material,weight_kg
T-Shirt,Coton Français,coton,0.25
Jeans,Denim Écologique,denim,0.50""".encode('utf-8')
        
        products = csv_adapter.parse(csv)
        assert len(products) == 2
        
        # Check accented characters preserved
        tshirt = next(p for p in products if p.name == "T-Shirt")
        assert tshirt.components[0].name == "Coton Français"
    
    def test_special_characters(self, csv_adapter):
        """Adapter should handle special characters in names."""
        csv = b"""product_name,component_name,material,weight_kg
Product-123,Component_ABC,material/type,0.25"""
        
        products = csv_adapter.parse(csv)
        assert products[0].name == "Product-123"
        assert products[0].components[0].name == "Component_ABC"
