"""NASA POWER API Agent - Fixed Wind Parameters"""

import requests
import logging
from typing import Dict, Any
from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability

logger = logging.getLogger("NASAAgent")


class NASAPowerAPI:
    """NASA POWER API Client"""
    
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    SOLAR_PARAMS = ["ALLSKY_SFC_SW_DWN"]
    
    # Fixed wind parameters (NASA updated their API)
    WIND_PARAMS = ["WS50M"]  # Use only WS50M (more reliable)
    
    @classmethod
    def fetch_solar_data(cls, latitude: float, longitude: float) -> Dict[str, Any]:
        """Fetch solar resource data."""
        params = {
            "parameters": ",".join(cls.SOLAR_PARAMS),
            "community": "RE",
            "longitude": longitude,
            "latitude": latitude,
            "start": "2022",
            "end": "2022",
            "format": "JSON"
        }
        
        try:
            logger.info(f"Fetching solar data for ({latitude}, {longitude})")
            response = requests.get(cls.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            ghi_data = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
            annual_avg_ghi = sum(ghi_data.values()) / len(ghi_data)
            
            logger.info(f"✓ Solar: {annual_avg_ghi:.2f} kWh/m²/day")
            
            return {
                "success": True,
                "ghi_kwh_m2_day": round(annual_avg_ghi, 2),
                "source": "NASA POWER"
            }
        except Exception as e:
            logger.error(f"Solar fetch failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    def fetch_wind_data(cls, latitude: float, longitude: float) -> Dict[str, Any]:
        """Fetch wind resource data."""
        params = {
            "parameters": ",".join(cls.WIND_PARAMS),
            "community": "RE",
            "longitude": longitude,
            "latitude": latitude,
            "start": "2022",
            "end": "2022",
            "format": "JSON"
        }
        
        try:
            logger.info(f"Fetching wind data for ({latitude}, {longitude})")
            response = requests.get(cls.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            ws50m_data = data["properties"]["parameter"]["WS50M"]
            annual_avg_ws50m = sum(ws50m_data.values()) / len(ws50m_data)
            
            # Estimate 100m wind speed (typically 1.2-1.3x higher)
            annual_avg_ws100m = annual_avg_ws50m * 1.25
            
            logger.info(f"✓ Wind: {annual_avg_ws100m:.2f} m/s at 100m (estimated)")
            
            return {
                "success": True,
                "wind_speed_50m_ms": round(annual_avg_ws50m, 2),
                "wind_speed_100m_ms": round(annual_avg_ws100m, 2),
                "source": "NASA POWER"
            }
        except Exception as e:
            logger.error(f"Wind fetch failed: {str(e)}")
            return {"success": False, "error": str(e)}


# Country locations
COUNTRY_LOCATIONS = {
    "USA": {
        "solar": {"lat": 36.0, "lon": -112.0, "name": "Arizona Solar Farm"},
        "wind": {"lat": 41.0, "lon": -100.0, "name": "Nebraska Wind Farm"}
    },
    "DEU": {
        "solar": {"lat": 51.0, "lon": 10.5, "name": "Bavaria Solar Park"},
        "wind": {"lat": 54.5, "lon": 9.0, "name": "North Sea Wind Farm"}
    },
    "IND": {
        "solar": {"lat": 23.0, "lon": 72.5, "name": "Gujarat Solar Park"},
        "wind": {"lat": 9.5, "lon": 77.5, "name": "Tamil Nadu Wind Farm"}
    },
    "CHN": {
        "solar": {"lat": 40.0, "lon": 116.0, "name": "Inner Mongolia Solar"},
        "wind": {"lat": 45.0, "lon": 125.0, "name": "Gansu Wind Base"}
    },
    "BRA": {
        "solar": {"lat": -10.0, "lon": -48.0, "name": "Bahia Solar Complex"},
        "wind": {"lat": -5.0, "lon": -37.5, "name": "Ceará Wind Farm"}
    }
}


@register_agent(
    agent_id="data_team_nasa_location_loader_v2",
    name="NASA Location Loader v2",
    description="Loads locations with real NASA POWER data (solar + wind)",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.DATA_FETCH],
    business_unit="data_team",
    contact="data@company.com",
    required_inputs=["countries"],
    output_keys=["locations"],
    timeout_seconds=120
)
def nasa_location_loader_v2(state: Dict[str, Any]) -> Dict[str, Any]:
    """Load representative locations with REAL NASA data."""
    countries = state.get("countries", [])
    locations = []
    
    for country_code in countries:
        if country_code not in COUNTRY_LOCATIONS:
            logger.warning(f"No locations for {country_code}")
            continue
        
        country_locs = COUNTRY_LOCATIONS[country_code]
        
        # Fetch solar data
        solar_loc = country_locs["solar"]
        solar_data = NASAPowerAPI.fetch_solar_data(solar_loc["lat"], solar_loc["lon"])
        
        if solar_data["success"]:
            locations.append({
                "country_code": country_code,
                "technology": "solar_pv",
                "name": solar_loc["name"],
                "latitude": solar_loc["lat"],
                "longitude": solar_loc["lon"],
                "resource_data": solar_data
            })
        
        # Fetch wind data
        wind_loc = country_locs["wind"]
        wind_data = NASAPowerAPI.fetch_wind_data(wind_loc["lat"], wind_loc["lon"])
        
        if wind_data["success"]:
            locations.append({
                "country_code": country_code,
                "technology": "onshore_wind",
                "name": wind_loc["name"],
                "latitude": wind_loc["lat"],
                "longitude": wind_loc["lon"],
                "resource_data": wind_data
            })
    
    logger.info(f"✓ Loaded {len(locations)} locations with NASA data")
    return {"locations": locations}


print("✅ NASA POWER Agent v2 registered!")
