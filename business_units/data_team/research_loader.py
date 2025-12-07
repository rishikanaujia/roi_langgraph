"""
Data Team - Research Data Loader (Phase 1)

Loads pre-researched country information from JSON into Phase 1 state.

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
- Integrates with Phase 1 state
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import (
    AgentFramework,
    AgentCapability,
    create_expert_metadata
)

logger = logging.getLogger("ResearchLoader")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

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
    "ind": "IND",

    "china": "CHN",
    "people's republic of china": "CHN",
    "prc": "CHN",
    "chn": "CHN",

    "brazil": "BRA",
    "brasil": "BRA",
    "federative republic of brazil": "BRA",
    "bra": "BRA",

    "germany": "DEU",
    "deutschland": "DEU",
    "federal republic of germany": "DEU",
    "deu": "DEU",

    "japan": "JPN",
    "nippon": "JPN",
    "jpn": "JPN",

    "united kingdom": "GBR",
    "uk": "GBR",
    "great britain": "GBR",
    "britain": "GBR",
    "gbr": "GBR",

    "france": "FRA",
    "french republic": "FRA",
    "fra": "FRA",

    "canada": "CAN",
    "can": "CAN",

    "australia": "AUS",
    "commonwealth of australia": "AUS",
    "aus": "AUS",

    "south africa": "ZAF",
    "republic of south africa": "ZAF",
    "zaf": "ZAF",

    "mexico": "MEX",
    "united mexican states": "MEX",
    "mex": "MEX",

    "spain": "ESP",
    "kingdom of spain": "ESP",
    "esp": "ESP",

    "italy": "ITA",
    "italian republic": "ITA",
    "ita": "ITA",
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
    skipped = []

    for idx, item in enumerate(json_data):
        try:
            # Validate structure
            if not isinstance(item, dict):
                logger.warning(f"Item {idx}: Skipping non-dict item: {type(item)}")
                skipped.append(f"Item {idx}: Not a dictionary")
                continue

            if 'country_name' not in item:
                logger.warning(f"Item {idx}: Missing 'country_name' key")
                skipped.append(f"Item {idx}: Missing 'country_name'")
                continue

            if 'research' not in item:
                logger.warning(f"Item {idx}: Missing 'research' key")
                skipped.append(f"Item {idx}: Missing 'research'")
                continue

            # Get country code
            country_name = item['country_name']
            country_code = normalize_country_name(country_name)

            if not country_code:
                logger.warning(
                    f"Item {idx}: Could not normalize country name: '{country_name}'. "
                    f"Add to COUNTRY_NAME_TO_CODE if needed."
                )
                skipped.append(f"Item {idx}: Unknown country '{country_name}'")
                continue

            # Store research
            research_text = item['research']

            if not research_text or not research_text.strip():
                logger.warning(f"Item {idx}: Empty research for {country_code}")
                skipped.append(f"Item {idx}: Empty research for {country_code}")
                continue

            research_by_country[country_code] = research_text.strip()

            logger.info(
                f"✅ Loaded research for {country_code} "
                f"({len(research_text)} chars)"
            )

        except Exception as e:
            logger.error(f"Item {idx}: Error processing: {str(e)}")
            skipped.append(f"Item {idx}: {str(e)}")
            continue

    if skipped:
        logger.warning(f"Skipped {len(skipped)} items during loading")

    return research_by_country


def load_research_from_file(file_path: str) -> tuple[Dict[str, str], List[str]]:
    """
    Load research data from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Tuple of (research_by_country, errors)
    """
    errors = []

    try:
        if not os.path.exists(file_path):
            error = f"File not found: {file_path}"
            logger.error(error)
            errors.append(error)
            return {}, errors

        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        if not isinstance(json_data, list):
            error = f"JSON must be a list of objects, got {type(json_data)}"
            logger.error(error)
            errors.append(error)
            return {}, errors

        logger.info(f"📄 Loaded {len(json_data)} items from {file_path}")

        research = load_research_from_json(json_data)
        return research, errors

    except json.JSONDecodeError as e:
        error = f"Invalid JSON in {file_path}: {str(e)}"
        logger.error(error)
        errors.append(error)
        return {}, errors

    except Exception as e:
        error = f"Error loading {file_path}: {str(e)}"
        logger.error(error)
        errors.append(error)
        return {}, errors


# ============================================================================
# Registered Agent
# ============================================================================

@register_agent(
    agent_id="data_team_research_loader_phase1_v1",
    name="Research Data Loader (Phase 1)",
    description="Loads pre-researched country information from JSON into Phase 1 state",
    framework=AgentFramework.CUSTOM,
    capabilities=[AgentCapability.RESEARCH],
    business_unit="data_team",
    contact="data@company.com",
    version="1.0.0",
    required_inputs=[],  # Optional: countries, research_json_path, research_json_data
    output_keys=["country_research", "research_metadata"],
    tags=["research", "json", "loader", "phase1"]
)
def research_loader(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load research data for countries into Phase 1 state.

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

    start_time = datetime.now()

    # Get input
    json_path = state.get("research_json_path")
    json_data = state.get("research_json_data")
    filter_countries = state.get("countries", [])

    logger.info("=" * 70)
    logger.info("RESEARCH LOADER - Starting...")
    logger.info("=" * 70)

    # Load research
    research_by_country = {}
    errors = []
    source = "none"

    if json_data:
        # Use provided JSON data
        logger.info("📊 Loading from provided JSON data")
        research_by_country = load_research_from_json(json_data)
        source = "direct_json_data"

    elif json_path:
        # Load from specified file
        logger.info(f"📄 Loading from file: {json_path}")
        research_by_country, file_errors = load_research_from_file(json_path)
        errors.extend(file_errors)
        source = json_path

    else:
        # Try default location
        default_path = "data/research.json"
        if os.path.exists(default_path):
            logger.info(f"📄 Loading from default location: {default_path}")
            research_by_country, file_errors = load_research_from_file(default_path)
            errors.extend(file_errors)
            source = default_path
        else:
            warning = (
                "No research data provided. "
                "Use research_json_path or research_json_data"
            )
            logger.warning(warning)
            errors.append(warning)

    # Filter to requested countries if specified
    if filter_countries:
        original_count = len(research_by_country)
        research_by_country = {
            code: text
            for code, text in research_by_country.items()
            if code in filter_countries
        }
        filtered_count = len(research_by_country)
        logger.info(
            f"🔍 Filtered from {original_count} to {filtered_count} countries"
        )

        # Check for missing countries
        missing = set(filter_countries) - set(research_by_country.keys())
        if missing:
            warning = f"Missing research for: {list(missing)}"
            logger.warning(warning)
            errors.append(warning)

    # Calculate stats
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    total_chars = sum(len(text) for text in research_by_country.values())
    avg_chars = total_chars / len(research_by_country) if research_by_country else 0

    # Create metadata
    metadata = {
        "countries_loaded": list(research_by_country.keys()),
        "total_countries": len(research_by_country),
        "total_characters": total_chars,
        "avg_characters_per_country": int(avg_chars),
        "source": source,
        "loader_version": "1.0.0",
        "loading_time_seconds": round(duration, 2),
        "timestamp": end_time.isoformat(),
        "errors": errors
    }

    # Log summary
    logger.info("=" * 70)
    logger.info(f"✅ RESEARCH LOADED - {metadata['total_countries']} countries")
    logger.info("=" * 70)

    for code, text in sorted(research_by_country.items()):
        logger.info(f"  • {code}: {len(text):,} characters")

    logger.info(f"\n📊 Total: {total_chars:,} characters")
    logger.info(f"⏱️  Time: {duration:.2f}s")

    if errors:
        logger.warning(f"⚠️  Errors: {len(errors)}")
        for error in errors:
            logger.warning(f"   - {error}")

    return {
        "country_research": research_by_country,
        "research_metadata": metadata
    }


# ============================================================================
# Module Setup
# ============================================================================

# Create business unit directory
os.makedirs("business_units/data_team", exist_ok=True)
with open("business_units/data_team/__init__.py", "w") as f:
    f.write("# Data Team - Research Loader\n")

logger.info("✅ Research Data Loader (Phase 1) registered!")
logger.info("   📄 Loads country research from JSON")
logger.info("   🗺️  Normalizes country names to codes")
logger.info("   📊 Supports file or direct JSON input")
logger.info("   🔍 Validates and filters data")