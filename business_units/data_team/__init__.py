"""
Data Team - Data Loading Agents

This team handles all data ingestion:
- NASA POWER API (solar/wind resource data)
- Research data from JSON files
"""

# Import agents to trigger registration
from . import nasa_location_loader
from . import research_loader

__all__ = ['nasa_location_loader', 'research_loader']
