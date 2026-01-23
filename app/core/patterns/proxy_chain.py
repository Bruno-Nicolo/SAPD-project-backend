from abc import ABC, abstractmethod
from typing import Any
import time


class DataHandler(ABC):
    def __init__(self):
        self._next_handler: DataHandler | None = None

    def set_next(self, handler: "DataHandler") -> "DataHandler":
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        pass


class RealDataHandler(DataHandler):
    def __init__(self, data_source: dict[str, Any]):
        super().__init__()
        self._data_source = data_source

    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        supplier_id = request.get("supplier_id")
        if supplier_id and supplier_id in self._data_source:
            return {"source": "real", "data": self._data_source[supplier_id]}
        if self._next_handler:
            return self._next_handler.handle(request)
        return {"source": "none", "data": None}


class AIEstimationHandler(DataHandler):
    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        estimated_data = {
            "supplier_name": f"AI_Estimated_{request.get('supplier_id', 'unknown')}",
            "carbon_footprint_kg": 3.5,
            "certifications": [],
            "is_estimated": True,
        }
        return {"source": "ai_estimation", "data": estimated_data}


class CachingProxy:
    def __init__(self, handler: DataHandler, ttl_seconds: int = 300):
        self._handler = handler
        self._cache: dict[str, tuple[dict[str, Any], float]] = {}
        self._ttl_seconds = ttl_seconds

    def get_data(self, request: dict[str, Any]) -> dict[str, Any]:
        cache_key = str(sorted(request.items()))
        current_time = time.time()

        if cache_key in self._cache:
            cached_result, cached_at = self._cache[cache_key]
            if current_time - cached_at < self._ttl_seconds:
                return {**cached_result, "cached": True}

        result = self._handler.handle(request)
        self._cache[cache_key] = (result, current_time)
        return {**result, "cached": False}

    def invalidate_cache(self) -> None:
        self._cache.clear()
