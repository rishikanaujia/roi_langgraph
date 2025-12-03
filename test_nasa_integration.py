"""Test NASA POWER API integration."""

from src.workflows.country_comparison_graph import CountryComparisonWorkflow
from src.registry.agent_registry import get_registry

# Import NASA agent
import business_units.data_team.nasa_agent
import business_units.ranking_team.agents


def test_nasa_workflow():
    """Test workflow with real NASA data."""
    
    print("="*70)
    print("🌍 NASA POWER API INTEGRATION TEST")
    print("="*70)
    
    # Show registered agents
    registry = get_registry()
    print("\n📊 Registered Agents:")
    registry.print_summary()
    
    # Create workflow
    print("\n🔧 Creating workflow...")
    workflow = CountryComparisonWorkflow()
    
    # Run with real NASA data!
    print("\n🚀 Fetching REAL data from NASA POWER API...")
    print("⏳ This may take 30-60 seconds (NASA API is slow)...\n")
    
    result = workflow.run(
        countries=["USA", "DEU"],  # Start with 2 countries
        query="Compare solar and wind resources"
    )
    
    # Display results
    print("\n" + "="*70)
    print("📊 RESULTS WITH REAL NASA DATA")
    print("="*70)
    
    for code, report in result['country_reports'].items():
        print(f"\n🌍 {code}:")
        for analysis in report.get('location_analyses', []):
            loc = analysis['location']
            resource = loc.get('resource_data', {})
            
            print(f"  📍 {loc['name']}")
            print(f"     Technology: {loc['technology']}")
            print(f"     Coordinates: ({loc['latitude']}, {loc['longitude']})")
            
            if loc['technology'] == 'solar_pv':
                ghi = resource.get('ghi_kwh_m2_day', 0)
                print(f"     ☀️  GHI: {ghi} kWh/m²/day")
            else:
                ws = resource.get('wind_speed_100m_ms', 0)
                print(f"     💨 Wind Speed (100m): {ws} m/s")
            
            print(f"     Source: {resource.get('source', 'N/A')}")
    
    print("\n" + "="*70)
    print("✅ NASA INTEGRATION TEST PASSED!")
    print("="*70)


if __name__ == "__main__":
    test_nasa_workflow()
