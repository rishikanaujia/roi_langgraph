"""
Research Data Service

Handles country name normalization and research data generation.
"""

from typing import List, Dict

# Country name to code mapping
COUNTRY_MAPPING = {
    "USA": "USA",
    "UNITED STATES": "USA",
    "US": "USA",
    "INDIA": "IND",
    "IND": "IND",
    "CHINA": "CHN",
    "CHN": "CHN",
    "BRAZIL": "BRA",
    "BRA": "BRA",
    "GERMANY": "DEU",
    "DEU": "DEU",
    "JAPAN": "JPN",
    "JPN": "JPN",
    "UK": "GBR",
    "UNITED KINGDOM": "GBR",
    "GBR": "GBR",
    "FRANCE": "FRA",
    "FRA": "FRA",
    "CANADA": "CAN",
    "CAN": "CAN",
    "AUSTRALIA": "AUS",
    "AUS": "AUS",
    "SOUTH AFRICA": "ZAF",
    "ZAF": "ZAF",
    "MEXICO": "MEX",
    "MEX": "MEX",
    "SPAIN": "ESP",
    "ESP": "ESP",
    "ITALY": "ITA",
    "ITA": "ITA"
}

# Research data templates
RESEARCH_TEMPLATES = {
    "USA": "The United States offers exceptional renewable energy opportunities with strong IRA policy support (30% ITC, production tax credits), world-class solar resources (6-7 kWh/m²/day in Southwest), robust wind potential (especially offshore on East Coast), mature grid infrastructure, $100+ billion annual market, and comprehensive regulatory framework. Key opportunities include grid modernization, energy storage deployment, and green hydrogen production.",

    "IND": "India presents compelling growth opportunities with ambitious 500 GW renewable target by 2030, Production-Linked Incentive (PLI) scheme for manufacturing, excellent solar resources in Gujarat/Rajasthan regions, significant wind potential in Tamil Nadu/Gujarat, growing grid infrastructure, and strong government commitment. Challenges include financing availability, land acquisition complexity, and grid integration needs.",

    "CHN": "China dominates global renewable manufacturing with world's largest solar capacity (400+ GW), massive wind deployment (350+ GW), complete supply chain integration, strong government support, aggressive deployment targets, and unmatched scale. However, market access for foreign investors remains limited, regulatory framework is complex, and geopolitical considerations add uncertainty.",

    "BRA": "Brazil offers excellent wind resources in Northeast region, strong hydro-wind complementarity, growing solar deployment, stable regulatory framework with auction system, and abundant land availability. Key challenges include transmission infrastructure gaps, currency volatility, and financing costs.",

    "DEU": "Germany provides stable policy environment with Energiewende commitment, strong Renewable Energy Sources Act (EEG), excellent wind resources in North Sea, robust grid infrastructure, and mature market. Challenges include permitting complexity, grid congestion, and phase-out of support mechanisms.",

    "JPN": "Japan offers stable regulatory environment, feed-in tariff system, growing offshore wind potential, and strong technology development. Challenges include limited land availability, high costs, complex permitting, and grid constraints.",

    "GBR": "United Kingdom excels in offshore wind with world-class resources, Contract for Difference (CfD) auction system, strong grid infrastructure, and ambitious net-zero targets. Opportunities include floating offshore wind and green hydrogen production.",

    "FRA": "France provides stable policy framework, growing solar deployment, offshore wind opportunities, strong grid infrastructure, and government support for energy transition. Nuclear energy dominance creates unique market dynamics.",

    "CAN": "Canada offers excellent wind and solar resources, stable policy environment, provincial renewable targets, abundant land, and strong grid infrastructure. Opportunities include grid-scale storage and green hydrogen for export.",

    "AUS": "Australia boasts world-class solar and wind resources, abundant land availability, growing market scale, and export opportunities for green hydrogen. Challenges include grid infrastructure gaps and market fragmentation.",

    "ZAF": "South Africa provides excellent solar resources, Renewable Energy Independent Power Producer Procurement Programme (REIPPPP), growing market, and strong project pipeline. Challenges include grid instability, policy uncertainty, and currency risk.",

    "MEX": "Mexico offers excellent solar resources in Sonora/Chihuahua, strong wind potential in Oaxaca/Istmo, growing market scale, and proximity to US market. Recent policy changes have created regulatory uncertainty.",

    "ESP": "Spain provides excellent solar resources, mature wind market, stable regulatory framework, strong grid infrastructure, and growing energy storage deployment. Recent auction successes demonstrate market strength.",

    "ITA": "Italy offers strong solar deployment, growing wind market, supportive regulatory framework, and EU funding opportunities. Grid infrastructure constraints and permitting complexity remain challenges."
}


def normalize_country_code(country: str) -> str:
    """Normalize country name to 3-letter code."""
    country_upper = country.strip().upper()
    return COUNTRY_MAPPING.get(country_upper, country_upper)


def generate_research_data(countries: List[str]) -> List[Dict[str, str]]:
    """Generate research data for countries."""
    research_data = []

    for country in countries:
        country_code = normalize_country_code(country)

        # Get research or use generic template
        research = RESEARCH_TEMPLATES.get(
            country_code,
            f"{country} renewable energy sector presents investment opportunities. "
            f"Detailed research data would be provided based on comprehensive market analysis, "
            f"policy framework review, resource assessment, and risk evaluation."
        )

        research_data.append({
            "country_name": country,
            "research": research
        })

    return research_data