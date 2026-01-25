from abc import ABC, abstractmethod

from app.core.patterns.composite import ProductComponent


class ScoringStrategy(ABC):
    @abstractmethod
    def calculate_score(self, component: ProductComponent) -> float:
        pass


class HiggIndexStrategy(ScoringStrategy):
    def calculate_score(self, component: ProductComponent) -> float:
        """
        Method 1: Inspired by the Higg Materials Sustainability Index (MSI).
        Considers multiple environmental impacts (CO2, Water, Energy) and weighs them.
        Higher is better (0-100).
        """
        factors = component.get_impact_factors()
        weight_kg = factors.get("weight_kg", 1.0)
        if weight_kg <= 0:
            weight_kg = 1.0
        
        # Relative impacts (per kg)
        energy_per_kg = factors.get("energy", 0.0) / weight_kg
        water_per_kg = factors.get("water", 0.0) / weight_kg
        
        # CO2 is calculated from energy (1 MJ ~ 0.15 kg CO2)
        co2_per_kg = energy_per_kg * 0.15

        # Higg Weights
        co2_weight = 0.45
        water_weight = 0.30
        energy_weight = 0.25
        
        # Benchmarks (poor performance values)
        MAX_CO2 = 15.0
        MAX_WATER = 500.0
        MAX_ENERGY = 100.0

        # Sub-scores (0-100)
        co2_score = max(0, 100 - (co2_per_kg / MAX_CO2 * 100))
        water_score = max(0, 100 - (water_per_kg / MAX_WATER * 100))
        energy_score = max(0, 100 - (energy_per_kg / MAX_ENERGY * 100))

        final_score = (co2_score * co2_weight) + \
                      (water_score * water_weight) + \
                      (energy_score * energy_weight)
                           
        return round(final_score, 2)


class CarbonFootprintStrategy(ScoringStrategy):
    def calculate_score(self, component: ProductComponent) -> float:
        """
        Method 2: Focused exclusively on carbon footprint.
        Starts from 100 and penalizes based on kg of CO2 emitted.
        CO2 emission is derived from energy consumption (1 MJ ~ 0.15 kg CO2).
        Higher is better (0-100).
        """
        factors = component.get_impact_factors()
        weight_kg = factors.get("weight_kg", 1.0)
        if weight_kg <= 0:
            weight_kg = 1.0
            
        energy_per_kg = factors.get("energy", 0.0) / weight_kg
        
        # 1 MJ energy consumption ~ 0.15 kg CO2e
        co2_per_kg = energy_per_kg * 0.15
        
        BASE_SCORE = 100.0
        PENALTY_FACTOR = 12.0 # Penalty points per kg CO2/kg product
        
        total_penalty = co2_per_kg * PENALTY_FACTOR
        final_score = BASE_SCORE - total_penalty
        
        return round(max(0, min(100, final_score)), 2)


class CircularEconomyStrategy(ScoringStrategy):
    def calculate_score(self, component: ProductComponent) -> float:
        """
        Method 3: Focused on recycling and waste (Circular Economy).
        Rewards recycled content and recyclability, penalizes waste.
        Higher is better (0-100).
        """
        factors = component.get_impact_factors()
        weight_kg = factors.get("weight_kg", 1.0)
        if weight_kg <= 0:
            weight_kg = 1.0

        recyclability = factors.get("recyclability", 0.0)
        recycled_content = factors.get("recycled_content", 0.0)
        waste_per_kg = factors.get("waste", 0.0) / weight_kg
        
        # Normalize to 0-100 scale
        recyclability_norm = recyclability * 100 if recyclability <= 1 else recyclability
        content_norm = recycled_content * 100 if recycled_content <= 1 else recycled_content

        # 1. Input Value: % of recycled material (Weight: 50%)
        # 2. Output Value: ease of recycling (Weight: 50%)
        base_circularity_score = (content_norm * 0.5) + (recyclability_norm * 0.5)
        
        # 3. Waste Penalty: MAX_WASTE (critical value)
        MAX_WASTE = 2.0  # kg of waste per kg of product
        waste_score = max(0, 100 - (waste_per_kg / MAX_WASTE * 100))
        
        # Weighted average between base circularity and waste management
        final_score = (base_circularity_score * 0.6) + (waste_score * 0.4)
        
        return round(max(0, min(100, final_score)), 2)


class CustomStrategy(ScoringStrategy):
    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or {}

    def calculate_score(self, component: ProductComponent) -> float:
        """
        Calculate score using custom weights for impact factors.
        Starts from 100 (Perfect) and subtracts penalties.
        """
        factors = component.get_impact_factors()
        
        score = 100.0
        
        weight = factors.get("weight_kg", 1.0)
        weight_kg = weight if weight > 0 else 1.0
        
        if weight_kg <= 0: return 0.0

        # Impacts (Penalties) - normalized per kg
        energy_impact = (factors.get("energy", 0.0) / weight_kg) * self.weights.get("energy", 0.0)
        water_impact = (factors.get("water", 0.0) / weight_kg) * self.weights.get("water", 0.0)
        waste_impact = (factors.get("waste", 0.0) / weight_kg) * self.weights.get("waste", 0.0)
        
        score -= (energy_impact + water_impact + waste_impact)
        
        # Benefits (Bonuses)
        score += factors.get("recyclability", 0.0) * self.weights.get("recyclability", 0.0)
        score += factors.get("recycled_content", 0.0) * self.weights.get("recycled_content", 0.0)
        
        return score


class ScoringContext:
    def __init__(self, strategy: ScoringStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: ScoringStrategy) -> None:
        self._strategy = strategy

    def calculate(self, component: ProductComponent) -> float:
        return self._strategy.calculate_score(component)
