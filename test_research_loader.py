"""
Test Research Data Loader

Tests the research loader agent with sample data.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.registry.agent_registry import AgentRegistry
from business_units.data_team import research_loader


def main():
    """Test research loader with sample data."""
    
    print("=" * 70)
    print("🧪 RESEARCH LOADER TEST")
    print("=" * 70)
    print()
    
    # Sample research data
    sample_data = [
        {
            "country_name": "United States",
            "research": """The United States renewable energy sector is experiencing 
            rapid growth driven by the Inflation Reduction Act (IRA). The IRA provides 
            30% Investment Tax Credit (ITC) for solar projects and Production Tax Credit 
            (PTC) for wind projects. Key states include California, Texas, and Iowa. 
            Federal support combined with state-level renewable portfolio standards creates 
            a favorable investment climate."""
        },
        {
            "country_name": "India",
            "research": """India has set ambitious renewable energy targets of 500 GW 
            by 2030. The PLI (Production-Linked Incentive) scheme offers capital subsidies 
            for solar manufacturing. Gujarat and Rajasthan are leading solar states, 
            while Tamil Nadu leads in wind energy. Recent policy changes include the Green 
            Energy Open Access Rules making it easier for commercial consumers to source 
            renewable energy."""
        },
        {
            "country_name": "China",
            "research": """China is the world's largest renewable energy market with 
            over 1,000 GW of installed capacity. The country dominates solar panel 
            manufacturing and wind turbine production. Key provinces include Qinghai, 
            Gansu, and Inner Mongolia for solar and wind development. China's 14th 
            Five-Year Plan emphasizes renewable energy with targets of 1,200 GW by 2030."""
        },
        {
            "country_name": "Brazil",
            "research": """Brazil's renewable energy sector is growing rapidly with 
            strong wind resources in the Northeast and excellent solar potential in 
            the Southeast. Recent energy auctions have driven competitive pricing. 
            The country aims for 23% of its energy matrix from non-hydro renewables by 2030. 
            The free market (ACL) for energy trading is expanding, offering corporate PPAs."""
        }
    ]
    
    print("📊 Test 1: Load from direct JSON data")
    print("-" * 70)
    
    # Test with direct JSON data
    state = {
        "research_json_data": sample_data
    }
    
    result = research_loader.research_loader(state)
    
    research = result.get('country_research', {})
    metadata = result.get('research_metadata', {})
    
    print(f"\n✓ Countries loaded: {metadata.get('total_countries', 0)}")
    print(f"✓ Total characters: {metadata.get('total_characters', 0):,}")
    print(f"✓ Source: {metadata.get('source', 'unknown')}")
    
    print("\n📄 Research by country:")
    for code, text in research.items():
        print(f"\n{code}:")
        print(f"  Length: {len(text):,} characters")
        preview = text.replace('\n', ' ').strip()[:100]
        print(f"  Preview: {preview}...")
    
    print("\n" + "-" * 70)
    print("📊 Test 2: Filter to specific countries")
    print("-" * 70)
    
    # Test with country filter
    state = {
        "research_json_data": sample_data,
        "countries": ["USA", "IND"]
    }
    
    result = research_loader.research_loader(state)
    research = result.get('country_research', {})
    
    print(f"\n✓ Filtered to: {list(research.keys())}")
    print(f"✓ Countries: {len(research)}")
    
    print("\n" + "-" * 70)
    print("📊 Test 3: Load from file (if exists)")
    print("-" * 70)
    
    # Test with file (if data/research.json exists)
    if os.path.exists("data/research.json"):
        state = {
            "research_json_path": "data/research.json",
            "countries": ["USA", "BRA", "DEU"]
        }
        
        result = research_loader.research_loader(state)
        research = result.get('country_research', {})
        metadata = result.get('research_metadata', {})
        
        print(f"\n✓ Loaded from file: data/research.json")
        print(f"✓ Countries: {list(research.keys())}")
        print(f"✓ Total characters: {metadata.get('total_characters', 0):,}")
    else:
        print("\n⚠️  data/research.json not found (optional)")
    
    print("\n" + "=" * 70)
    print("✅ RESEARCH LOADER TEST COMPLETE!")
    print("=" * 70)
    print()
    print("📋 Next Steps:")
    print("   1. Create data/research.json with your research data")
    print("   2. Integrate into workflow")
    print("   3. Pass research to insights agents for richer analysis")
    print()


if __name__ == "__main__":
    main()
