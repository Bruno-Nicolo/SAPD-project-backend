from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class SupplierData:
    supplier_name: str
    material: str
    origin_country: str
    carbon_footprint_kg: float
    certifications: list[str]


class SupplyChainDataProvider(ABC):
    @abstractmethod
    def fetch_data(self, supplier_id: str) -> SupplierData:
        pass


class RestApiAdapter(SupplyChainDataProvider):
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url

    def fetch_data(self, supplier_id: str) -> SupplierData:
        return SupplierData(
            supplier_name=f"RestSupplier_{supplier_id}",
            material="organic_cotton",
            origin_country="IT",
            carbon_footprint_kg=2.5,
            certifications=["GOTS", "FairTrade"],
        )


class LegacyDatabaseAdapter(SupplyChainDataProvider):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def fetch_data(self, supplier_id: str) -> SupplierData:
        return SupplierData(
            supplier_name=f"LegacySupplier_{supplier_id}",
            material="polyester",
            origin_country="CN",
            carbon_footprint_kg=5.0,
            certifications=[],
        )


class CsvFileAdapter(SupplyChainDataProvider):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def fetch_data(self, supplier_id: str) -> SupplierData:
        return SupplierData(
            supplier_name=f"CsvSupplier_{supplier_id}",
            material="recycled_polyester",
            origin_country="DE",
            carbon_footprint_kg=1.8,
            certifications=["OekoTex"],
        )


class SupplyChainFacade:
    def __init__(self):
        self._providers: dict[str, SupplyChainDataProvider] = {}

    def register_provider(self, name: str, provider: SupplyChainDataProvider) -> None:
        self._providers[name] = provider

    def get_supplier_data(self, provider_name: str, supplier_id: str) -> SupplierData:
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not registered")
        return self._providers[provider_name].fetch_data(supplier_id)

    def get_aggregated_carbon_footprint(self, supplier_ids: dict[str, list[str]]) -> float:
        total = 0.0
        for provider_name, ids in supplier_ids.items():
            for supplier_id in ids:
                data = self.get_supplier_data(provider_name, supplier_id)
                total += data.carbon_footprint_kg
        return total
