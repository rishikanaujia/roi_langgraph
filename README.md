roi_langgraph/
├── src/
│   ├── registry/
│   │   ├── __init__.py
│   │   ├── agent_registry.py          # Universal agent catalog
│   │   └── agent_metadata.py          # Agent descriptions
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base_adapter.py            # Base adapter interface
│   │   ├── langchain_adapter.py       # LangChain agent wrapper
│   │   ├── langgraph_adapter.py       # LangGraph agent wrapper
│   │   └── custom_adapter.py          # Custom agent wrapper
│   ├── state/
│   │   ├── __init__.py
│   │   └── shared_state.py            # LangGraph state definition
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── country_comparison_graph.py # Main LangGraph workflow
│   │   └── conditional_edges.py       # Routing logic
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── plugin_interface.py        # Plugin contract
│   │   └── sample_plugin.py           # Example plugin
│   └── api/
│       ├── __init__.py
│       └── routes.py                  # FastAPI endpoints
├── business_units/                     # Each BU adds their agents here
│   ├── research_team/
│   │   └── agents.py                  # Research team's agents
│   ├── analysis_team/
│   │   └── agents.py                  # Analysis team's agents
│   └── ranking_team/
│       └── agents.py                  # Ranking team's agents
├── tests/
│   └── test_integration.py
└── requirements.txt


## 📋 ARCHITECTURE OVERVIEW

┌─────────────────────────────────────────────────────────┐
│         LANGGRAPH MULTI-AGENT ORCHESTRATION             │
└─────────────────────────────────────────────────────────┘

Business Unit Agents (Easy Integration)
  ↓
┌─────────────────────────────────────────────────────────┐
│  UNIVERSAL AGENT REGISTRY                               │
│  • Research Team Agents (LangChain)                     │
│  • Analysis Team Agents (LangGraph)                     │
│  • Ranking Team Agents (Custom)                         │
│  • External Team Agents (Any framework)                 │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│  AGENT ADAPTERS (Normalize Different Types)             │
│  • LangChain Agent Adapter                              │
│  • LangGraph Agent Adapter                              │
│  • Custom Agent Adapter                                 │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│  LANGGRAPH STATE GRAPH (Orchestration)                  │
│  • Shared State                                         │
│  • Agent Routing                                        │
│  • Conditional Edges                                    │
│  • Human-in-the-loop                                    │
└─────────────────────────────────────────────────────────┘
  ↓
Output (Same as current system)