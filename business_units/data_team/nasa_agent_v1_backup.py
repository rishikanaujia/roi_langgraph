"""
NASA POWER API Agent

Fetches real solar and wind resource data from NASA POWER API.
"""

import requests
import logging
from typing import Dict, Any, List
from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability

logger = logging.getLogger("NASAAgent")


class NASAPowerAPI:
    """
    NASA POWER API Client
    
    Fetches renewable energy resource data.
    API Docs: https://power.larc.nasa.gov/docs/services/api/
    """
    
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    # Solar parameters
    SOLAR_PARAMS = [
        "ALLSKY_SFC_SW_DWN",  # All Sky Surface Shortwave Downward Irradiance
        "CLRSKY_SFC_SW_DWN",  # Clear Sky Surface Shortwave Downward Irradiance
    ]
    
    # Wind parameters
    WIND_PARAMS = [
        "WS50M",   # Wind Speed at 50m
        "WS100M",  # Wind Speed at 100m
    ]
    
    @classmethod
    def fetch_solar_data(
        cls,
        latitude: float,
        longitude: float,
        start_date: str = "2022",
        end_date: str = "2022"
    ) -> Dict[str, Any]:
        """
        Fetch solar resource data for a location.
        
        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            start_date: Start year (YYYY)
            end_date: End year (YYYY)
        
        Returns:
            Dict with solar resource data
        """
        params = {
            "parameters": ",".join(cls.SOLAR_PARAMS),
            "community": "RE",
            "longitude": longitude,
            "latitude": latitude,
            "start": start_date,
            "end": end_date,
            "format": "JSON"
        }
        
        try:
            logger.info(f"Fetching solar data for ({latitude}, {longitude})")
            response = requests.get(cls.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate annual average GHI
            ghi_data = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
            annual_avg_ghi = sum(ghi_data.values()) / len(ghi_data)
            
            logger.info(f"✓ Solar data fetched: {annual_avg_ghi:.2f} kWh/m²/day")
            
            return {
                "success": True,
                "latitude": latitude,
                "longitude": longitude,
                "ghi_kwh_m2_day": round(annual_avg_ghi, 2),
                "data_year": start_date,
                "source": "NASA POWER"
            }
        
        except Exception as e:
            logger.error(f"Failed to fetch solar data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "latitude": latitude,
                "longitude": longitude
            }
    
    @classmethod
    def fetch_wind_data(
        cls,
        latitude: float,
        longitude: float,
        start_date: str = "2022",
        end_date: str = "2022"
    ) -> Dict[str, Any]:
        """
        Fetch wind resource data for a location.
        
        Args:
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            start_date: Start year (YYYY)
            end_date: End year (YYYY)
        
        Returns:
            Dict with wind resource data
        """
        params = {
            "parameters": ",".join(cls.WIND_PARAMS),
            "community": "RE",
            "longitude": longitude,
            "latitude": latitude,
            "start": start_date,
            "end": end_date,
            "format": "JSON"
        }
        
        try:
            logger.info(f"Fetching wind data for ({latitude}, {longitude})")
            response = requests.get(cls.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate annual average wind speeds
            ws50m_data = data["properties"]["parameter"]["WS50M"]
            ws100m_data = data["properties"]["parameter"]["WS100M"]
            
            annual_avg_ws50m = sum(ws50m_data.values()) / len(ws50m_data)
            annual_avg_ws100m = sum(ws100m_data.values()) / len(ws100m_data)
            
            logger.info(f"✓ Wind data fetched: {annual_avg_ws100m:.2f} m/s at 100m")
            
            return {
                "success": True,
                "latitude": latitude,
                "longitude": longitude,
                "wind_speed_50m_ms": round(annual_avg_ws50m, 2),
                "wind_speed_100m_ms": round(annual_avg_ws100m, 2),
                "data_year": start_date,
                "source": "NASA POWER"
            }
        
        except Exception as e:
            logger.error(f"Failed to fetch wind data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "latitude": latitude,
                "longitude": longitude
            }


# Representative locations for each country
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
    },
    "AUS": {
        "solar": {"lat": -27.5, "lon": 133.0, "name": "Northern Territory Solar"},
        "wind": {"lat": -38.0, "lon": 145.0, "name": "Victoria Wind Farm"}
    },
    "GBR": {
        "solar": {"lat": 51.5, "lon": -0.5, "name": "South England Solar"},
        "wind": {"lat": 55.0, "lon": -3.0, "name": "Scottish Highlands Wind"}
    },
    "CAN": {
        "solar": {"lat": 51.0, "lon": -114.0, "name": "Alberta Solar"},
        "wind": {"lat": 50.0, "lon": -97.0, "name": "Manitoba Wind"}
    },
    "FRA": {
        "solar": {"lat": 45.0, "lon": 2.0, "name": "Southern France Solar"},
        "wind": {"lat": 47.5, "lon": -3.0, "name": "Brittany Wind Farm"}
    },
    "JPN": {
        "solar": {"lat": 35.0, "lon": 138.0, "name": "Yamanashi Solar"},
        "wind": {"lat": 40.5, "lon": 140.0, "name": "Aomori Wind Farm"}
    }
}


@register_agent(
    agent_id="data_team_nasa_location_loader_v1",
    name="NASA Location Loader",
    description="Loads representative locations with real NASA POWER data",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.DATA_FETCH],
    business_unit="data_team",
    contact="data@company.com",
    required_inputs=["countries"],
    output_keys=["locations"],
    timeout_seconds=120  # NASA API can be slow
)
def nasa_location_loader(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load representative locations with REAL NASA data.
    
    Replaces mock location loader in workflow.
    """
    countries = state.get("countries", [])
    
    locations = []
    
    for country_code in countries:
        if country_code not in COUNTRY_LOCATIONS:
            logger.warning(f"No locations defined for {country_code}, skipping")
            continue
        
        country_locs = COUNTRY_LOCATIONS[country_code]
        
        # Solar location
        solar_loc = country_locs["solar"]
        solar_data = NASAPowerAPI.fetch_solar_data(
            solar_loc["lat"],
            solar_loc["lon"]
        )
        
        if solar_data["success"]:
            locations.append({
                "country_code": country_code,
                "technology": "solar_pv",
                "name": solar_loc["name"],
                "latitude": solar_loc["lat"],
                "longitude": solar_loc["lon"],
                "resource_data": solar_data
            })
        
        # Wind location
        wind_loc = country_locs["wind"]
        wind_data = NASAPowerAPI.fetch_wind_data(
            wind_loc["lat"],
            wind_loc["lon"]
        )
        
        if wind_data["success"]:
            locations.append({
                "country_code": country_code,
                "technology": "onshore_wind",
                "name": wind_loc["name"],
                "latitude": wind_loc["lat"],
                "longitude": wind_loc["lon"],
                "resource_data": wind_data
            })
    
    logger.info(f"✓ Loaded {len(locations)} locations with real NASA data")
    
    return {"locations": locations}


print("✅ NASA POWER Agent registered!")
