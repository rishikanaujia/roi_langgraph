"""
Research Service - Country Research Data Generation

Provides research data for renewable energy investment analysis.

Features:
- Country name normalization (United States → USA)
- Pre-written research templates for 14 countries
- Mock data generation for testing
- Supports both country names and codes
"""

import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger("ResearchService")
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
    "rsa": "ZAF",
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

VALID_COUNTRY_CODES = set(COUNTRY_NAME_TO_CODE.values())

# ============================================================================
# Country Research Templates
# ============================================================================

COUNTRY_RESEARCH_DATA = {
    "USA": """The United States offers exceptional renewable energy opportunities with strong policy support through the Inflation Reduction Act (IRA) providing 30% Investment Tax Credits (ITC) and Production Tax Credits (PTC). The country boasts world-class solar resources averaging 6-7 kWh/m²/day in the Southwest, robust wind potential especially offshore on the East Coast with capacity factors exceeding 40%, and mature grid infrastructure with active transmission expansion. The market size exceeds $100 billion annually with sustained 15-20% growth, supported by comprehensive regulatory frameworks at federal and state levels including renewable portfolio standards in 30+ states. Key investment opportunities include utility-scale solar with falling costs below $30/MWh, offshore wind development with 30GW pipeline, battery storage deployment with $369B IRA support, and green hydrogen initiatives. Major challenges include transmission bottlenecks requiring $100B+ investment, permitting delays averaging 3-5 years, supply chain dependencies on imports, and policy uncertainty around federal support. The investment climate is highly favorable with established markets, transparent regulations, strong rule of law, and proven technology deployment at scale.""",

    "IND": """India presents compelling growth opportunities with an ambitious 500 GW renewable energy target by 2030, comprising 280 GW solar and 140 GW wind capacity. The Production-Linked Incentive (PLI) scheme allocates ₹24,000 crore for solar manufacturing, while excellent solar resources in Gujarat and Rajasthan regions deliver 5.5-6.5 kWh/m²/day. Significant wind potential exists in Tamil Nadu, Gujarat, and Karnataka with capacity factors of 25-35%. The growing grid infrastructure is supported by Green Energy Corridors Phase II investing ₹12,000 crore in transmission. Strong government commitment is demonstrated through National Solar Mission, target of 50% electric capacity from renewables by 2030, and simplified approval processes. Key opportunities include solar manufacturing with PLI incentives and local content requirements, distributed solar reaching 40 GW rooftop target, pumped hydro storage with 27 GW under development, and green hydrogen with National Hydrogen Mission targeting 5 MMT production. Challenges include grid integration with balancing needs, land acquisition difficulties in dense regions, payment delays from distribution companies, and tariff pressures driving costs below ₹2/kWh. The regulatory environment features competitive bidding for price discovery, long-term PPAs providing revenue certainty, and SEZs offering tax benefits, though permitting complexity remains at state level.""",

    "CHN": """China dominates global renewable manufacturing and deployment with the world's largest solar capacity exceeding 400 GW and massive wind deployment surpassing 350 GW. The country maintains complete supply chain integration from polysilicon to modules, supported by strong government backing through 14th Five Year Plan targeting 1,200 GW total renewable capacity by 2030. Aggressive deployment continues with 200+ GW annual additions and substantial cost advantages in manufacturing. Manufacturing excellence is demonstrated through polysilicon production controlling 80%+ global supply, solar cell efficiency exceeding 25%, wind turbine production at 60% global market share, and battery dominance with 75% global capacity. Unmatched scale advantages include economies of scale in production, vertical integration reducing costs, established export networks, and R&D investment exceeding $50B annually. Investment opportunities focus on supply chain expansion in raw materials and components, next-generation technologies including perovskite and floating solar, energy storage deployment with 100 GW target by 2030, and green hydrogen production for industrial decarbonization. Key challenges include overcapacity risks in solar and wind manufacturing, grid curtailment with 3-5% waste rates, market access barriers for foreign investors, and policy shifts around subsidy reductions. The regulatory framework features central planning with clear targets, state-owned enterprise dominance, local content requirements, and limited foreign ownership with JV requirements.""",

    "BRA": """Brazil offers exceptional renewable resources with world-class wind speeds in the Northeast region averaging 7-9 m/s, abundant solar irradiation reaching 5-6 kWh/m²/day across most regions, massive hydroelectric capacity of 109 GW providing flexibility, and extensive bioenergy potential from sugarcane bagasse. Government support includes BNDES financing at favorable rates, tax incentives for renewable projects including REIDI tax relief, and net metering for distributed generation. The market shows strong growth with 30 GW renewable capacity target by 2030, auction mechanisms ensuring transparent price discovery, and growing corporate PPAs from industrial demand. Key opportunities exist in wind power expansion with 30+ GW pipeline in Northeast, solar deployment including 20 GW distributed generation target, biomass cogeneration utilizing sugar industry infrastructure, and hybrid projects combining wind, solar, and hydro. Challenges include transmission constraints requiring new lines, regulatory uncertainty around policy changes, currency volatility affecting returns, and permitting complexity across federal and state levels. The investment climate features mature auction system with competitive pricing, strong rule of law and contract enforcement, established project finance market, though bureaucracy and lengthy approval processes remain concerns.""",

    "DEU": """Germany demonstrates renewable energy leadership with Energiewende transition policy targeting 80% renewable electricity by 2030, strong industrial base for technology manufacturing, robust R&D ecosystem with Fraunhofer institutes, and mature regulatory framework through EEG feed-in tariffs. Excellent wind resources exist in North Sea and Baltic Sea offshore locations with capacity factors exceeding 45%, while solar deployment continues despite moderate irradiation of 3.5-4.5 kWh/m²/day. Advanced grid infrastructure features intelligent network management, cross-border integration with European neighbors, and innovative storage solutions. Key opportunities include offshore wind with 30 GW target by 2030, green hydrogen economy with €9B National Hydrogen Strategy, energy storage deployment for grid balancing, and building integration of solar PV and heat pumps. Investment strengths include technological innovation in power-to-X and sector coupling, skilled workforce and engineering expertise, stable political and regulatory environment, and access to European capital markets. Challenges involve high costs with electricity prices among highest in Europe, land constraints for onshore development in densely populated areas, phase-out of nuclear creating gaps, and transmission bottlenecks between North and South. The regulatory environment features competitive auctions replacing feed-in tariffs, grid connection guarantees for renewables, carbon pricing at €50-60/ton, though permitting delays average 4-6 years for onshore wind.""",

    "JPN": """Japan presents unique renewable opportunities driven by post-Fukushima nuclear reduction targets aiming for 36-38% renewable electricity by 2030, strong technology innovation in solar panel efficiency and battery storage, corporate renewable demand with RE100 commitments, and government support through feed-in tariffs. Limited land availability drives floating solar innovation with largest global installations, offshore wind potential with 90 GW target leveraging deep water technology, and geothermal resources with 23 GW potential utilizing volcanic activity. Key opportunities include offshore wind development with auction framework launched, floating solar systems on reservoirs and coastal waters, battery storage with vehicle-to-grid integration, and green hydrogen imports supporting decarbonization targets. Strengths include high electricity prices supporting renewable economics, technological leadership in efficiency and innovation, reliable grid infrastructure, and strong corporate commitment to sustainability. Challenges involve high development costs due to land prices and construction, complex permitting requiring multiple agencies, grid constraints on isolated networks, and typhoon risks requiring robust engineering. The investment climate features FIT/FIP mechanisms transitioning to auctions, corporate PPAs becoming more common, stable regulatory environment, though high costs and slow approvals pose barriers.""",

    "GBR": """The United Kingdom excels in offshore wind leadership with 14 GW installed capacity targeting 50 GW by 2030, successful CfD auction mechanism delivering competitive prices below £40/MWh, strong policy commitment through Net Zero Strategy by 2050, and growing floating wind technology in Scottish waters. Excellent offshore wind resources exist in North Sea, Irish Sea, and Atlantic approaches with capacity factors exceeding 50%. Emerging opportunities include floating offshore wind with 5 GW target, green hydrogen production with 10 GW electrolyzer capacity by 2030, and carbon capture integration with industrial clusters. Key investment opportunities span offshore wind farm development in ScotWind and Celtic Sea, hydrogen economy buildout in industrial regions, battery storage supporting grid flexibility, and tidal energy in Pentland Firth. Strengths include proven auction system driving cost reduction, stable political commitment across parties, mature supply chain for offshore development, and access to capital markets. Challenges involve grid reinforcement needs for offshore transmission, supply chain capacity constraints, planning consent complexity, and port infrastructure requirements. The regulatory framework features CfD providing revenue certainty, Contracts for Difference auction rounds, planning streamlining for offshore projects, and carbon pricing at £30-40/ton.""",

    "FRA": """France pursues renewable expansion with targets of 40% renewable electricity by 2030, strong nuclear base providing low-carbon foundation at 70% generation, government support through PPE multi-annual energy plan, and European integration enabling trade and balancing. Solar development opportunities exist despite moderate 3.5-4.5 kWh/m²/day resources, with rooftop and agrivoltaics potential. Offshore wind development targets 6.2 GW by 2028 in Channel and Atlantic sites, while onshore wind faces public acceptance challenges. Key opportunities include solar deployment with simplified authorization, floating offshore wind technology development, green hydrogen in industrial applications, and biomass from agricultural resources. Investment strengths include stable regulatory environment, government backing through ADEME support, skilled workforce in nuclear and renewables, and access to European markets. Challenges involve nuclear dominance limiting market prices, complex permitting requiring local consultation, grid integration with existing infrastructure, and public opposition to onshore wind. The regulatory framework features feed-in tariffs transitioning to auctions, PPE providing policy visibility, carbon pricing via EU ETS, though bureaucracy and approval times remain concerns.""",

    "CAN": """Canada offers vast renewable potential with exceptional hydroelectric resources providing 60% of generation capacity, strong wind resources across prairies and coastlines averaging 7-8 m/s, growing solar deployment despite northern latitude challenges, and abundant biomass from forestry. Provincial leadership drives development with Alberta's renewables program, Quebec's hydroelectric expansion, and Ontario's nuclear phase-out creating opportunities. Strong ESG demand comes from corporate buyers and pension funds prioritizing sustainability. Key opportunities include wind power expansion in Alberta and Saskatchewan, solar growth in southern provinces, small modular reactors for remote communities, and green hydrogen leveraging low-cost electricity. Strengths include low-cost hydroelectric providing baseload, stable political environment and rule of law, skilled workforce and engineering expertise, and proximity to US markets. Challenges involve transmission distances in vast geography, provincial jurisdiction creating regulatory fragmentation, cold climate impacts on performance, and indigenous consultation requirements. The investment climate features provincial power purchase agreements, federal Clean Electricity Regulations, carbon pricing at CAD $65/ton and rising, and streamlined approvals in some provinces.""",

    "AUS": """Australia possesses world-class solar resources averaging 5.5-7 kWh/m²/day across most regions, excellent wind resources in southern and coastal areas, abundant land availability for large-scale projects, and strong mining sector demand for renewable power. Rooftop solar leadership shows 30% household penetration with 3.5 million installations, while grid transformation is driven by coal retirement creating 15+ GW replacement need. Export opportunities emerge with green hydrogen targeting Asian markets and renewable electricity via subsea cables. Key investment opportunities include utility-scale solar and wind with LCOE below AUD $40/MWh, battery storage supporting grid stability, green hydrogen production for export and domestic use, and renewable energy zones in NSW and Victoria. Strengths include exceptional resource quality, competitive costs among world's lowest, strong rule of law and contract enforcement, and growing corporate demand. Challenges involve grid instability from coal closures, transmission investment needs exceeding AUD $10B, policy uncertainty around federal support, and gas transition debates. The regulatory framework features competitive tenders in some states, underwriting mechanisms for stability, state-level targets and auctions, though federal policy remains inconsistent.""",

    "ZAF": """South Africa presents unique opportunities with exceptional solar resources averaging 6-7 kWh/m²/day among world's best, strong wind resources on coastal regions, coal transition creating 20+ GW replacement opportunity from aging fleet, and REIPPP program demonstrating successful procurement. Government support includes REIPPP competitive bidding framework, Eskom grid access commitments, policy support through IRP2019, and municipal procurement rights. Key opportunities span utility-scale solar and wind at highly competitive costs, wheeling and private PPAs enabled by policy changes, battery storage for grid support, and green hydrogen leveraging low-cost renewables. Investment strengths include proven procurement system, excellent resource quality, competitive pricing below ZAR 0.60/kWh, and growing private sector demand. Challenges involve Eskom financial crisis affecting offtake, transmission constraints and grid reliability, currency volatility impacting returns, and permitting delays. The regulatory framework features REIPPP auctions with transparent process, wheeling regulations enabling private sales, carbon tax at ZAR 134/ton, though policy implementation and grid access remain uncertain.""",

    "MEX": """Mexico offers strong solar resources averaging 5.5-6.5 kWh/m²/day especially in northern states, good wind resources on Isthmus of Tehuantepec and coastal areas, large industrial demand from manufacturing sector, and proximity to US markets enabling potential trade. Previous auction success demonstrated competitive prices below USD $20/MWh, while nearshoring trends drive increased electricity demand. Corporate PPAs show strong industrial buyer interest. Key opportunities include utility-scale solar in Sonora and Chihuahua, wind development in Oaxaca and coastal regions, distributed generation for commercial and industrial users, and cross-border renewable energy trade. Strengths include excellent resource quality, industrial electricity demand growth, strategic location for US market access, and competitive labor costs. Challenges involve significant policy uncertainty under current administration, CFE monopoly strengthening, auction suspension since 2018, and permitting obstacles for private projects. The investment climate shows previous auction framework now suspended, limited new project approvals, legacy contracts grandfathered, though uncertainty around future policy direction creates risks.""",

    "ESP": """Spain demonstrates renewable leadership with 50% renewable electricity generation achieved, ambitious targets of 74% by 2030, successful auction history delivering low prices, and strong solar resources averaging 5-6 kWh/m²/day. Excellent wind resources exist in northern and central regions, while established manufacturing base supports local supply chain. Recovery plan allocates €10B+ in green investments. Key opportunities include solar deployment with significant pipeline, wind repowering of aging assets, battery storage for grid integration, and green hydrogen with 4 GW target by 2030. Investment strengths include mature market with proven track record, competitive economics among Europe's lowest costs, EU recovery funds supporting investment, and simplified administrative procedures. Challenges involve grid constraints requiring transmission upgrades, retroactive policy changes creating historical concerns, permitting delays despite improvements, and cannibalization risk from high solar penetration. The regulatory framework features competitive auctions with long-term visibility, merchant market opportunities growing, grid connection improvements underway, though historical regulatory changes remain a concern.""",

    "ITA": """Italy pursues renewable growth with 65% renewable electricity target by 2030, strong solar resources averaging 4.5-5.5 kWh/m²/day especially in southern regions, high electricity prices supporting project economics, and recovery plan funding €5.9B for renewables. Distributed generation thrives with rooftop solar potential, while agrivoltaics gain momentum combining agriculture and energy. Key opportunities include utility-scale solar in southern regions, floating PV on reservoirs and water bodies, offshore wind in southern seas, and energy communities enabled by new regulations. Investment strengths include high power prices improving returns, EU recovery funds available, growing corporate PPA market, and established supply chain. Challenges involve complex permitting across regions and municipalities, grid constraints in southern areas, land use conflicts, and regional regulatory differences. The regulatory framework features feed-in tariffs being phased out, auction mechanisms introduced, simplified procedures for small projects, though bureaucracy and approval times remain significant barriers.""",
}


# ============================================================================
# Helper Functions
# ============================================================================

def normalize_country_code(country: str) -> Optional[str]:
    """
    Convert country name to ISO 3166-1 alpha-3 code.

    Args:
        country: Country name or code (case-insensitive)

    Returns:
        Three-letter country code (e.g., "USA") or None if not found

    Examples:
        >>> normalize_country_code("United States")
        "USA"
        >>> normalize_country_code("India")
        "IND"
        >>> normalize_country_code("usa")
        "USA"
    """
    if not country:
        logger.warning("Empty country name provided")
        return None

    # Normalize: lowercase, strip whitespace
    normalized = country.lower().strip()

    # Check if already a valid country code (3 letters)
    if len(normalized) == 3 and normalized.upper() in VALID_COUNTRY_CODES:
        return normalized.upper()

    # Look up in mapping
    code = COUNTRY_NAME_TO_CODE.get(normalized)

    if not code:
        logger.warning(f"Unrecognized country: '{country}'")
        return None

    return code


def get_supported_countries() -> List[str]:
    """
    Get list of all supported country codes.

    Returns:
        List of ISO 3166-1 alpha-3 country codes

    Example:
        >>> countries = get_supported_countries()
        >>> print(countries)
        ['USA', 'IND', 'CHN', ...]
    """
    return sorted(list(VALID_COUNTRY_CODES))


def get_country_name(country_code: str) -> Optional[str]:
    """
    Get full country name from code.

    Args:
        country_code: Three-letter country code

    Returns:
        Full country name or None if not found

    Example:
        >>> get_country_name("USA")
        "United States"
    """
    # Reverse lookup
    code_to_name = {
        "USA": "United States",
        "IND": "India",
        "CHN": "China",
        "BRA": "Brazil",
        "DEU": "Germany",
        "JPN": "Japan",
        "GBR": "United Kingdom",
        "FRA": "France",
        "CAN": "Canada",
        "AUS": "Australia",
        "ZAF": "South Africa",
        "MEX": "Mexico",
        "ESP": "Spain",
        "ITA": "Italy"
    }

    return code_to_name.get(country_code.upper())


# ============================================================================
# Main Research Data Functions
# ============================================================================

def generate_research_data(countries: List[str]) -> List[Dict[str, str]]:
    """
    Generate research data for a list of countries.

    Args:
        countries: List of country names or codes

    Returns:
        List of dictionaries with 'country_name' and 'research' keys

    Example:
        >>> data = generate_research_data(["USA", "India", "China"])
        >>> print(data[0])
        {
            "country_name": "United States",
            "research": "The United States offers..."
        }
    """

    logger.info("=" * 70)
    logger.info(f"GENERATING RESEARCH DATA FOR {len(countries)} COUNTRIES")
    logger.info("=" * 70)

    research_data = []

    for country in countries:
        # Normalize country name to code
        country_code = normalize_country_code(country)

        if not country_code:
            logger.warning(f"Skipping unrecognized country: '{country}'")
            continue

        # Get research text
        research_text = COUNTRY_RESEARCH_DATA.get(country_code)

        if not research_text:
            logger.warning(f"No research data available for: {country_code}")
            # Generate generic placeholder
            research_text = f"Research data for {country_code} is currently unavailable. This is a placeholder for future content."

        # Get full country name
        country_name = get_country_name(country_code) or country_code

        research_data.append({
            "country_name": country_name,
            "research": research_text
        })

        logger.info(f"✅ Generated research for {country_code} ({len(research_text)} chars)")

    logger.info("=" * 70)
    logger.info(f"✅ RESEARCH DATA GENERATED FOR {len(research_data)} COUNTRIES")
    logger.info("=" * 70)

    return research_data


def get_research_for_country(country: str) -> Optional[str]:
    """
    Get research data for a single country.

    Args:
        country: Country name or code

    Returns:
        Research text or None if not available

    Example:
        >>> research = get_research_for_country("USA")
        >>> print(research[:100])
        "The United States offers exceptional renewable energy opportunities..."
    """

    country_code = normalize_country_code(country)

    if not country_code:
        logger.warning(f"Cannot get research for unrecognized country: '{country}'")
        return None

    research = COUNTRY_RESEARCH_DATA.get(country_code)

    if not research:
        logger.warning(f"No research data available for: {country_code}")
        return None

    return research


def validate_countries(countries: List[str]) -> tuple[List[str], List[str]]:
    """
    Validate and normalize a list of countries.

    Args:
        countries: List of country names or codes

    Returns:
        Tuple of (valid_codes, invalid_countries)

    Example:
        >>> valid, invalid = validate_countries(["USA", "XYZ", "India"])
        >>> print(valid)
        ["USA", "IND"]
        >>> print(invalid)
        ["XYZ"]
    """

    valid_codes = []
    invalid_countries = []

    for country in countries:
        code = normalize_country_code(country)

        if code and code in COUNTRY_RESEARCH_DATA:
            valid_codes.append(code)
        else:
            invalid_countries.append(country)

    return valid_codes, invalid_countries


def get_research_summary() -> Dict[str, Any]:
    """
    Get summary statistics about available research data.

    Returns:
        Dictionary with research statistics

    Example:
        >>> summary = get_research_summary()
        >>> print(summary)
        {
            "total_countries": 14,
            "countries": ["USA", "IND", ...],
            "avg_length": 1523,
            "total_length": 21322
        }
    """

    countries = list(COUNTRY_RESEARCH_DATA.keys())
    lengths = [len(text) for text in COUNTRY_RESEARCH_DATA.values()]

    return {
        "total_countries": len(countries),
        "countries": sorted(countries),
        "avg_length": sum(lengths) // len(lengths) if lengths else 0,
        "total_length": sum(lengths),
        "min_length": min(lengths) if lengths else 0,
        "max_length": max(lengths) if lengths else 0
    }


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "generate_research_data",
    "get_research_for_country",
    "normalize_country_code",
    "validate_countries",
    "get_supported_countries",
    "get_country_name",
    "get_research_summary",
    "VALID_COUNTRY_CODES",
    "COUNTRY_NAME_TO_CODE"
]