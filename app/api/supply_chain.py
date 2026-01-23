from fastapi import APIRouter

from app.core.patterns.adapter_facade import (
    SupplyChainFacade,
    RestApiAdapter,
    LegacyDatabaseAdapter,
    CsvFileAdapter,
)
from app.core.patterns.proxy_chain import (
    RealDataHandler,
    AIEstimationHandler,
    CachingProxy,
)

router = APIRouter(prefix="/supply-chain", tags=["supply-chain"])

facade = SupplyChainFacade()
facade.register_provider("rest_api", RestApiAdapter("https://api.supplier.example.com"))
facade.register_provider("legacy_db", LegacyDatabaseAdapter("postgresql://legacy-db"))
facade.register_provider("csv", CsvFileAdapter("/data/suppliers.csv"))

real_data_source = {
    "SUP001": {"supplier_name": "EcoTextiles", "carbon_footprint_kg": 1.5},
    "SUP002": {"supplier_name": "GreenFabrics", "carbon_footprint_kg": 2.0},
}

real_handler = RealDataHandler(real_data_source)
ai_handler = AIEstimationHandler()
real_handler.set_next(ai_handler)

caching_proxy = CachingProxy(real_handler, ttl_seconds=300)


@router.get("/supplier/{provider_name}/{supplier_id}")
def get_supplier_data(provider_name: str, supplier_id: str):
    try:
        data = facade.get_supplier_data(provider_name, supplier_id)
        return {"provider": provider_name, "supplier_id": supplier_id, "data": data}
    except ValueError as e:
        return {"error": str(e)}


@router.get("/data/{supplier_id}")
def get_data_with_fallback(supplier_id: str):
    request = {"supplier_id": supplier_id}
    result = caching_proxy.get_data(request)
    return result


@router.post("/cache/invalidate")
def invalidate_cache():
    caching_proxy.invalidate_cache()
    return {"message": "Cache invalidated"}
