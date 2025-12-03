"""
Research Team Agents

Example: How the Research Team can integrate their LangChain agents.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool

from src.registry.agent_registry import register_agent
from src.registry.agent_metadata import AgentFramework, AgentCapability
from src.adapters.langchain_adapter import wrap_langchain_agent


# ============ EXAMPLE 1: LangChain Agent with Tools ============

def create_research_agent_with_tools():
    """
    Research team's LangChain agent with custom tools.

    This agent can:
    - Fetch policy data
    - Fetch resource data
    - Search documents
    """

    # Define tools
    def fetch_policy_data(country_code: str) -> str:
        """Fetch renewable energy policy data for a country."""
        # In real system, this would query a database
        policies = {
            "USA": "IRA provides 30% ITC for solar, PTC for wind",
            "DEU": "EEG 2023 provides feed-in tariffs",
            "IND": "PLI scheme offers capital subsidies"
        }
        return policies.get(country_code, "No policy data available")

    def fetch_resource_data(location: Dict[str, Any]) -> str:
        """Fetch solar/wind resource data for a location."""
        # In real system, this would call NASA POWER API
        return f"GHI: 5.5 kWh/m²/day, Wind: 7.5 m/s at 100m"

    # Create LangChain tools
    tools = [
        Tool(
            name="fetch_policy_data",
            func=fetch_policy_data,
            description="Fetch renewable energy policy data for a country"
        ),
        Tool(
            name="fetch_resource_data",
            func=lambda x: fetch_resource_data({}),
            description="Fetch solar/wind resource data for a location"
        )
    ]

    # Create LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a renewable energy research assistant. "
                   "Use the provided tools to gather policy and resource data."),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    # Create agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    return agent_executor


# Register the LangChain agent
research_agent = create_research_agent_with_tools()
wrapped_research = wrap_langchain_agent(
    research_agent,
    input_key="query",
    output_key="research_result"
)

register_agent(
    agent_id="research_team_langchain_agent_v1",
    name="Research Agent (LangChain)",
    description="Fetches policy and resource data using LangChain agent with tools",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.RESEARCH, AgentCapability.DATA_FETCH],
    business_unit="research_team",
    contact="research@company.com",
    required_inputs=["query"],
    output_keys=["research_result"]
)(wrapped_research)

# ============ EXAMPLE 2: Simple LangChain Chain ============

from langchain.chains import LLMChain


def create_simple_research_chain():
    """Simple LangChain chain for document analysis."""

    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Analyze renewable energy policies and provide insights."),
        ("user", "{policy_text}")
    ])

    chain = LLMChain(llm=llm, prompt=prompt)
    return chain


# Register simple chain
simple_chain = create_simple_research_chain()
wrapped_chain = wrap_langchain_agent(
    simple_chain,
    input_key="policy_text",
    output_key="analysis"
)

register_agent(
    agent_id="research_team_policy_analyzer_v1",
    name="Policy Analyzer (LangChain)",
    description="Analyzes policy documents using LangChain",
    framework=AgentFramework.LANGCHAIN,
    capabilities=[AgentCapability.ANALYSIS],
    business_unit="research_team",
    contact="research@company.com",
    required_inputs=["policy_text"],
    output_keys=["analysis"]
)(wrapped_chain)

print("✅ Research Team agents registered!")