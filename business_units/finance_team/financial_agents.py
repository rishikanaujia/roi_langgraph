"""
Finance Team Agents - FIXED

Calculate IRR, LCOE, NPV based on real resource data.
"""

import logging
from typing import Dict, Any
from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability

logger = logging.getLogger("FinanceAgents")


class SolarFinancialModel:
    """Solar PV Financial Model"""
    
    CAPEX_USD_PER_KW = {
        "USA": 1200, "DEU": 1100, "IND": 900,
        "CHN": 800, "BRA": 1000, "default": 1100
    }
    
    OPEX_USD_PER_KW_YEAR = 20
    CAPACITY_MW = 50
    CAPACITY_FACTOR_BASE = 0.20
    DEGRADATION_RATE = 0.005
    PROJECT_LIFE_YEARS = 25
    DISCOUNT_RATE = 0.08
    
    PPA_RATE_USD_PER_MWH = {
        "USA": 60, "DEU": 80, "IND": 50,
        "CHN": 45, "BRA": 55, "default": 60
    }
    
    @classmethod
    def calculate_capacity_factor(cls, ghi_kwh_m2_day: float) -> float:
        """Calculate capacity factor from GHI."""
        return min((ghi_kwh_m2_day / 6.5) * cls.CAPACITY_FACTOR_BASE, 0.30)
    
    @classmethod
    def calculate_metrics(cls, country_code: str, ghi_kwh_m2_day: float) -> Dict[str, float]:
        """Calculate IRR, LCOE, NPV for solar project."""
        
        capex_per_kw = cls.CAPEX_USD_PER_KW.get(country_code, cls.CAPEX_USD_PER_KW["default"])
        ppa_rate = cls.PPA_RATE_USD_PER_MWH.get(country_code, cls.PPA_RATE_USD_PER_MWH["default"])
        
        capacity_factor = cls.calculate_capacity_factor(ghi_kwh_m2_day)
        total_capex = capex_per_kw * cls.CAPACITY_MW * 1000
        
        hours_per_year = 8760
        annual_generation_base = cls.CAPACITY_MW * hours_per_year * capacity_factor
        
        # Cash flows
        cash_flows = [-total_capex]
        
        for year in range(1, cls.PROJECT_LIFE_YEARS + 1):
            generation = annual_generation_base * ((1 - cls.DEGRADATION_RATE) ** (year - 1))
            revenue = generation * ppa_rate
            opex = cls.OPEX_USD_PER_KW_YEAR * cls.CAPACITY_MW * 1000
            cash_flow = revenue - opex
            cash_flows.append(cash_flow)
        
        # NPV
        npv = sum(cf / ((1 + cls.DISCOUNT_RATE) ** year) for year, cf in enumerate(cash_flows))
        
        # IRR
        irr = cls._calculate_irr(cash_flows)
        
        # LCOE
        total_costs = total_capex + sum(
            (cls.OPEX_USD_PER_KW_YEAR * cls.CAPACITY_MW * 1000) / ((1 + cls.DISCOUNT_RATE) ** year)
            for year in range(1, cls.PROJECT_LIFE_YEARS + 1)
        )
        total_generation = sum(
            annual_generation_base * ((1 - cls.DEGRADATION_RATE) ** (year - 1)) / ((1 + cls.DISCOUNT_RATE) ** year)
            for year in range(1, cls.PROJECT_LIFE_YEARS + 1)
        )
        lcoe = total_costs / total_generation
        
        return {
            "irr": round(irr, 2),
            "lcoe": round(lcoe, 2),
            "npv": round(npv, 0),
            "capacity_factor": round(capacity_factor, 3),
            "annual_generation_mwh": round(annual_generation_base, 0)
        }
    
    @staticmethod
    def _calculate_irr(cash_flows, iterations=100):
        """Calculate IRR using Newton-Raphson method."""
        irr_guess = 0.10
        
        for _ in range(iterations):
            npv = sum(cf / ((1 + irr_guess) ** year) for year, cf in enumerate(cash_flows))
            npv_derivative = sum(-year * cf / ((1 + irr_guess) ** (year + 1)) for year, cf in enumerate(cash_flows))
            
            if abs(npv_derivative) < 1e-10:
                break
            
            irr_guess = irr_guess - npv / npv_derivative
            
            if irr_guess < -0.99:
                return -50.0
        
        return irr_guess * 100


class WindFinancialModel:
    """Onshore Wind Financial Model"""
    
    CAPEX_USD_PER_KW = {
        "USA": 1500, "DEU": 1600, "IND": 1200,
        "CHN": 1100, "BRA": 1300, "default": 1400
    }
    
    OPEX_USD_PER_KW_YEAR = 35
    CAPACITY_MW = 100
    PROJECT_LIFE_YEARS = 25
    DISCOUNT_RATE = 0.08
    
    PPA_RATE_USD_PER_MWH = {
        "USA": 45, "DEU": 70, "IND": 40,
        "CHN": 35, "BRA": 42, "default": 50
    }
    
    @classmethod
    def calculate_capacity_factor(cls, wind_speed_100m_ms: float) -> float:
        """Calculate capacity factor from wind speed."""
        if wind_speed_100m_ms < 6:
            return max(0.15, 0.08 + (wind_speed_100m_ms - 6) * 0.02)
        else:
            return min(0.50, 0.20 + (wind_speed_100m_ms - 6) * 0.04)
    
    @classmethod
    def calculate_metrics(cls, country_code: str, wind_speed_100m_ms: float) -> Dict[str, float]:
        """Calculate IRR, LCOE, NPV for wind project."""
        
        capex_per_kw = cls.CAPEX_USD_PER_KW.get(country_code, cls.CAPEX_USD_PER_KW["default"])
        ppa_rate = cls.PPA_RATE_USD_PER_MWH.get(country_code, cls.PPA_RATE_USD_PER_MWH["default"])
        
        capacity_factor = cls.calculate_capacity_factor(wind_speed_100m_ms)
        total_capex = capex_per_kw * cls.CAPACITY_MW * 1000
        
        hours_per_year = 8760
        annual_generation = cls.CAPACITY_MW * hours_per_year * capacity_factor
        
        # Cash flows
        cash_flows = [-total_capex]
        
        for year in range(1, cls.PROJECT_LIFE_YEARS + 1):
            revenue = annual_generation * ppa_rate
            opex = cls.OPEX_USD_PER_KW_YEAR * cls.CAPACITY_MW * 1000
            cash_flow = revenue - opex
            cash_flows.append(cash_flow)
        
        npv = sum(cf / ((1 + cls.DISCOUNT_RATE) ** year) for year, cf in enumerate(cash_flows))
        irr = SolarFinancialModel._calculate_irr(cash_flows)
        
        total_costs = total_capex + sum(
            (cls.OPEX_USD_PER_KW_YEAR * cls.CAPACITY_MW * 1000) / ((1 + cls.DISCOUNT_RATE) ** year)
            for year in range(1, cls.PROJECT_LIFE_YEARS + 1)
        )
        total_generation = sum(
            annual_generation / ((1 + cls.DISCOUNT_RATE) ** year)
            for year in range(1, cls.PROJECT_LIFE_YEARS + 1)
        )
        lcoe = total_costs / total_generation
        
        return {
            "irr": round(irr, 2),
            "lcoe": round(lcoe, 2),
            "npv": round(npv, 0),
            "capacity_factor": round(capacity_factor, 3),
            "annual_generation_mwh": round(annual_generation, 0)
        }


@register_agent(
    agent_id="finance_team_single_location_analyzer_v1",
    name="Single Location Financial Analyzer",
    description="Analyzes ONE location's financial metrics (called per location)",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.ANALYSIS],
    business_unit="finance_team",
    contact="finance@company.com",
    required_inputs=["current_location"],  # Changed from "locations"
    output_keys=["irr", "lcoe", "npv", "capacity_factor", "annual_generation_mwh"]
)
def single_location_financial_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a SINGLE location's financial metrics.
    
    This is called once per location by the workflow.
    """
    # Get the current location being analyzed
    location = state.get("current_location")
    
    if not location:
        logger.error("No current_location in state!")
        return {}
    
    country_code = location.get("country_code", "default")
    technology = location.get("technology")
    resource_data = location.get("resource_data", {})
    
    logger.info(f"Analyzing {location.get('name')} ({technology})")
    
    if not resource_data.get("success"):
        logger.warning(f"No resource data for {location.get('name')}")
        return {
            "irr": 0.0,
            "lcoe": 0.0,
            "npv": 0.0,
            "capacity_factor": 0.0,
            "annual_generation_mwh": 0.0
        }
    
    # Calculate financial metrics based on technology
    try:
        if technology == "solar_pv":
            ghi = resource_data.get("ghi_kwh_m2_day", 0)
            if ghi == 0:
                raise ValueError("No GHI data")
            
            metrics = SolarFinancialModel.calculate_metrics(country_code, ghi)
            logger.info(f"✓ Solar {country_code}: IRR={metrics['irr']:.1f}%, "
                       f"LCOE=${metrics['lcoe']:.0f}/MWh, NPV=${metrics['npv']/1e6:.1f}M")
        
        elif technology == "onshore_wind":
            wind_speed = resource_data.get("wind_speed_100m_ms", 0)
            if wind_speed == 0:
                raise ValueError("No wind speed data")
            
            metrics = WindFinancialModel.calculate_metrics(country_code, wind_speed)
            logger.info(f"✓ Wind {country_code}: IRR={metrics['irr']:.1f}%, "
                       f"LCOE=${metrics['lcoe']:.0f}/MWh, NPV=${metrics['npv']/1e6:.1f}M")
        
        else:
            raise ValueError(f"Unknown technology: {technology}")
        
        return metrics
    
    except Exception as e:
        logger.error(f"Financial analysis failed for {location.get('name')}: {str(e)}")
        return {
            "irr": 0.0,
            "lcoe": 0.0,
            "npv": 0.0,
            "capacity_factor": 0.0,
            "annual_generation_mwh": 0.0
        }


# Create __init__.py
import os
os.makedirs("business_units/finance_team", exist_ok=True)
with open("business_units/finance_team/__init__.py", "w") as f:
    f.write("")

print("✅ Financial Analyzer registered!")
