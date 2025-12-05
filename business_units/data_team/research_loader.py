"""
Data Team - Research Data Loader

Loads pre-researched country information from JSON.

Input JSON format:
[
  {
    "country_name": "United States",
    "research": "Detailed research about renewable energy in USA..."
  },
  {
    "country_name": "India", 
    "research": "Detailed research about renewable energy in India..."
  }
]

Features:
- Loads from file path or direct JSON
- Normalizes country names to codes (United States -> USA)
- Validates JSON structure
- Returns research mapped by country code
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability

logger = logging.getLogger("ResearchLoader")


# ============================================================================
# Country Name Mapping
# ============================================================================

COUNTRY_NAME_TO_CODE = {
    # Full names
    "united states": "USA",
    "united states of america": "USA",
    "usa": "USA",
    "us": "USA",
    
    "india": "IND",
    "republic of india": "IND",
    
    "china": "CHN",
    "people's republic of china": "CHN",
    "prc": "CHN",
    
    "brazil": "BRA",
    "brasil": "BRA",
    "federative republic of brazil": "BRA",
    
    "germany": "DEU",
    "deutschland": "DEU",
    "federal republic of germany": "DEU",
    
    "japan": "JPN",
    "nippon": "JPN",
    
    "united kingdom": "GBR",
    "uk": "GBR",
    "great britain": "GBR",
    "britain": "GBR",
    
    "france": "FRA",
    "french republic": "FRA",
    
    "canada": "CAN",
    
    "australia": "AUS",
    "commonwealth of australia": "AUS",
    
    "south africa": "ZAF",
    "republic of south africa": "ZAF",
    
    "mexico": "MEX",
    "united mexican states": "MEX",
    
    "spain": "ESP",
    "kingdom of spain": "ESP",
    
    "italy": "ITA",
    "italian republic": "ITA",
}


def normalize_country_name(country_name: str) -> Optional[str]:
    """
    Convert country name to ISO 3166-1 alpha-3 code.
    
    Args:
        country_name: Country name (case-insensitive)
        
    Returns:
        Three-letter country code (e.g., "USA") or None if not found
    """
    if not country_name:
        return None
    
    # Normalize: lowercase, strip whitespace
    normalized = country_name.lower().strip()
    
    # Check if already a country code (3 letters)
    if len(normalized) == 3 and normalized.upper() in COUNTRY_NAME_TO_CODE.values():
        return normalized.upper()
    
    # Look up in mapping
    return COUNTRY_NAME_TO_CODE.get(normalized)


# ============================================================================
# Research Data Loader
# ============================================================================

def load_research_from_json(json_data: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Load research data from JSON structure.
    
    Args:
        json_data: List of dicts with 'country_name' and 'research' keys
        
    Returns:
        Dictionary mapping country codes to research text
        
    Example:
        Input:
        [
            {"country_name": "United States", "research": "US has strong..."},
            {"country_name": "India", "research": "India is growing..."}
        ]
        
        Output:
        {
            "USA": "US has strong...",
            "IND": "India is growing..."
        }
    """
    research_by_country = {}
    
    for item in json_data:
        try:
            # Validate structure
            if not isinstance(item, dict):
                logger.warning(f"Skipping non-dict item: {item}")
                continue
            
            if 'country_name' not in item:
                logger.warning(f"Skipping item without 'country_name': {item}")
                continue
            
            if 'research' not in item:
                logger.warning(f"Skipping item without 'research': {item}")
                continue
            
            # Get country code
            country_name = item['country_name']
            country_code = normalize_country_name(country_name)
            
            if not country_code:
                logger.warning(
                    f"Could not normalize country name: '{country_name}'. "
                    f"Add to COUNTRY_NAME_TO_CODE mapping if needed."
                )
                continue
            
            # Store research
            research_text = item['research']
            
            if not research_text or not research_text.strip():
                logger.warning(f"Empty research for {country_code}")
                continue
            
            research_by_country[country_code] = research_text.strip()
            
            logger.info(
                f"✓ Loaded research for {country_code} "
                f"({len(research_text)} chars)"
            )
        
        except Exception as e:
            logger.error(f"Error processing item {item}: {str(e)}")
            continue
    
    return research_by_country


def load_research_from_file(file_path: str) -> Dict[str, str]:
    """
    Load research data from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dictionary mapping country codes to research text
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        if not isinstance(json_data, list):
            raise ValueError(
                f"JSON must be a list of objects, got {type(json_data)}"
            )
        
        logger.info(f"Loaded {len(json_data)} items from {file_path}")
        
        return load_research_from_json(json_data)
    
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {}
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {str(e)}")
        return {}
    
    except Exception as e:
        logger.error(f"Error loading {file_path}: {str(e)}")
        return {}


# ============================================================================
# Registered Agent
# ============================================================================

@register_agent(
    agent_id="data_team_research_loader_v1",
    name="Research Data Loader",
    description="Loads pre-researched country information from JSON",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.DATA_FETCH],
    business_unit="data_team",
    contact="data@company.com",
    version="1.0.0",
    tags=["research", "json", "loader"]
)
def research_loader(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load research data for countries.
    
    Input (from state):
        - research_json_path (optional): Path to JSON file
        - research_json_data (optional): Direct JSON data
        - countries (optional): Filter to specific countries
    
    Output (to state):
        - country_research: Dict[country_code, research_text]
        - research_metadata: Loading stats
    
    Priority:
        1. research_json_data (if provided)
        2. research_json_path (if provided)
        3. Default: data/research.json (if exists)
    """
    
    # Get input
    json_path = state.get("research_json_path")
    json_data = state.get("research_json_data")
    filter_countries = state.get("countries", [])
    
    logger.info("🔍 Research Loader starting...")
    
    # Load research
    research_by_country = {}
    
    if json_data:
        # Use provided JSON data
        logger.info("Loading from provided JSON data")
        research_by_country = load_research_from_json(json_data)
    
    elif json_path:
        # Load from specified file
        logger.info(f"Loading from file: {json_path}")
        research_by_country = load_research_from_file(json_path)
    
    else:
        # Try default location
        default_path = "data/research.json"
        if os.path.exists(default_path):
            logger.info(f"Loading from default location: {default_path}")
            research_by_country = load_research_from_file(default_path)
        else:
            logger.warning(
                "No research data provided. "
                "Use research_json_path or research_json_data"
            )
    
    # Filter to requested countries if specified
    if filter_countries:
        research_by_country = {
            code: text 
            for code, text in research_by_country.items()
            if code in filter_countries
        }
        logger.info(f"Filtered to {len(research_by_country)} countries")
    
    # Create metadata
    metadata = {
        "countries_loaded": list(research_by_country.keys()),
        "total_countries": len(research_by_country),
        "total_characters": sum(len(text) for text in research_by_country.values()),
        "source": "json_data" if json_data else json_path or "default",
        "loader_version": "1.0.0"
    }
    
    logger.info(
        f"✓ Loaded research for {metadata['total_countries']} countries "
        f"({metadata['total_characters']:,} chars total)"
    )
    
    # Log summary
    for code, text in research_by_country.items():
        logger.info(f"  • {code}: {len(text):,} characters")
    
    return {
        "country_research": research_by_country,
        "research_metadata": metadata
    }


print("✅ Research Data Loader registered!")
print("   📄 Loads country research from JSON")
print("   🗺️  Normalizes country names to codes")
print("   📊 Supports file or direct JSON input")
