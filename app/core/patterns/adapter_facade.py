"""
Product File Adapter Pattern

Provides a common interface for parsing product data from different file formats.
Currently supports CSV, with the structure ready to add more formats (JSON, Excel, etc.)
"""
import csv
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ComponentData:
    """Parsed component data from file."""
    name: str
    material: str
    weight_kg: float
    energy_consumption_mj: float = 0.0
    water_usage_liters: float = 0.0
    waste_generation_kg: float = 0.0
    recyclability_score: float = 0.0
    recycled_content_percentage: float = 0.0


@dataclass
class ProductData:
    """Parsed product data from file."""
    name: str
    components: list[ComponentData]


class ProductFileAdapter(ABC):
    """
    Abstract base class for product file adapters.
    
    Each adapter knows how to parse a specific file format
    and return a standardized list of ProductData objects.
    """
    
    @abstractmethod
    def parse(self, content: bytes) -> list[ProductData]:
        """
        Parse file content and return list of product data.
        
        Args:
            content: Raw file bytes
            
        Returns:
            List of ProductData objects ready for database insertion
            
        Raises:
            ValueError: If file format is invalid or required columns are missing
        """
        pass
    
    @property
    @abstractmethod
    def supported_extension(self) -> str:
        """Return the file extension this adapter handles (e.g., '.csv')."""
        pass


class CsvProductAdapter(ProductFileAdapter):
    """
    Adapter for parsing CSV files containing product data.
    
    Expected CSV format:
    product_name,component_name,material,weight_kg[,optional_columns...]
    
    Optional columns:
    energy_consumption_mj, water_usage_liters, waste_generation_kg,
    recyclability_score, recycled_content_percentage
    
    Products with the same name are grouped together.
    """
    
    REQUIRED_COLUMNS = {'product_name', 'component_name', 'material', 'weight_kg'}
    
    @property
    def supported_extension(self) -> str:
        return '.csv'
    
    def parse(self, content: bytes) -> list[ProductData]:
        """Parse CSV content into ProductData objects."""
        decoded = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        
        # Validate required columns
        if not reader.fieldnames:
            raise ValueError("Empty CSV file")
        
        if not self.REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
            missing = self.REQUIRED_COLUMNS - set(reader.fieldnames)
            raise ValueError(f"CSV missing required columns: {', '.join(missing)}")
        
        # Group rows by product name
        products_dict: dict[str, list[ComponentData]] = {}
        
        for row in reader:
            product_name = row['product_name'].strip()
            if not product_name:
                continue
                
            if product_name not in products_dict:
                products_dict[product_name] = []
            
            component = ComponentData(
                name=row['component_name'].strip(),
                material=row['material'].strip(),
                weight_kg=self._parse_float(row.get('weight_kg', '0')),
                energy_consumption_mj=self._parse_float(row.get('energy_consumption_mj')),
                water_usage_liters=self._parse_float(row.get('water_usage_liters')),
                waste_generation_kg=self._parse_float(row.get('waste_generation_kg')),
                recyclability_score=self._parse_float(row.get('recyclability_score')),
                recycled_content_percentage=self._parse_float(row.get('recycled_content_percentage')),
            )
            products_dict[product_name].append(component)
        
        # Convert to ProductData list
        return [
            ProductData(name=name, components=components)
            for name, components in products_dict.items()
        ]
    
    @staticmethod
    def _parse_float(value: str | None) -> float:
        """Safely parse a float value, returning 0.0 on failure."""
        if not value or not value.strip():
            return 0.0
        try:
            return float(value)
        except ValueError:
            return 0.0


# Registry of available adapters
PRODUCT_FILE_ADAPTERS: dict[str, ProductFileAdapter] = {
    '.csv': CsvProductAdapter(),
}


def get_adapter_for_file(filename: str) -> ProductFileAdapter | None:
    """
    Get the appropriate adapter for a file based on its extension.
    
    Args:
        filename: Name of the file to parse
        
    Returns:
        Adapter instance if format is supported, None otherwise
    """
    ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return PRODUCT_FILE_ADAPTERS.get(ext)


def get_supported_formats() -> list[str]:
    """Return list of supported file extensions."""
    return list(PRODUCT_FILE_ADAPTERS.keys())
