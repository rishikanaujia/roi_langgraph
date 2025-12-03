"""
Universal Agent Registry

Central catalog where all business units register their agents.
Supports discovery, filtering, and retrieval of agents from any framework.
"""

from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
import logging
from datetime import datetime

from src.registry.agent_metadata import (
    AgentMetadata,
    AgentFramework,
    AgentCapability,
    AgentExecutionResult
)


class AgentRegistry:
    """
    Central registry for all agents across business units.

    Features:
    - Register agents from any framework
    - Discover agents by capability, business unit, or tags
    - Validate agent metadata
    - Track agent versions
    """

    def __init__(self):
        """Initialize empty registry."""
        self._agents: Dict[str, Dict[str, Any]] = {}  # agent_id -> {metadata, executor}
        self._by_capability: Dict[AgentCapability, List[str]] = defaultdict(list)
        self._by_business_unit: Dict[str, List[str]] = defaultdict(list)
        self._by_framework: Dict[AgentFramework, List[str]] = defaultdict(list)

        self.logger = logging.getLogger("AgentRegistry")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.info("Agent Registry initialized")

    def register_agent(
            self,
            metadata: AgentMetadata,
            executor: Callable
    ) -> None:
        """
        Register an agent in the registry.

        Args:
            metadata: Agent metadata (description, capabilities, etc.)
            executor: Callable that executes the agent
                     Signature: executor(state: Dict[str, Any]) -> Dict[str, Any]

        Raises:
            ValueError: If agent_id already exists or validation fails
        """
        # Validate
        if metadata.agent_id in self._agents:
            raise ValueError(
                f"Agent {metadata.agent_id} already registered. "
                f"Use update_agent() to modify."
            )

        if not callable(executor):
            raise ValueError("Executor must be callable")

        # Store agent
        self._agents[metadata.agent_id] = {
            "metadata": metadata,
            "executor": executor,
            "registered_at": datetime.now().isoformat()
        }

        # Index by capability
        for capability in metadata.capabilities:
            self._by_capability[capability].append(metadata.agent_id)

        # Index by business unit
        self._by_business_unit[metadata.business_unit].append(metadata.agent_id)

        # Index by framework
        self._by_framework[metadata.framework].append(metadata.agent_id)

        self.logger.info(
            f"✓ Registered agent: {metadata.agent_id} "
            f"({metadata.name}) from {metadata.business_unit}"
        )

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent by ID.

        Returns:
            Dict with 'metadata' and 'executor', or None if not found
        """
        return self._agents.get(agent_id)

    def get_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata by ID."""
        agent = self.get_agent(agent_id)
        return agent["metadata"] if agent else None

    def get_executor(self, agent_id: str) -> Optional[Callable]:
        """Get agent executor by ID."""
        agent = self.get_agent(agent_id)
        return agent["executor"] if agent else None

    def list_agents(
            self,
            capability: Optional[AgentCapability] = None,
            business_unit: Optional[str] = None,
            framework: Optional[AgentFramework] = None,
            enabled_only: bool = True
    ) -> List[AgentMetadata]:
        """
        List agents with optional filtering.

        Args:
            capability: Filter by capability
            business_unit: Filter by business unit
            framework: Filter by framework
            enabled_only: Only return enabled agents

        Returns:
            List of agent metadata
        """
        # Start with all agents
        agent_ids = set(self._agents.keys())

        # Apply filters
        if capability:
            agent_ids &= set(self._by_capability.get(capability, []))

        if business_unit:
            agent_ids &= set(self._by_business_unit.get(business_unit, []))

        if framework:
            agent_ids &= set(self._by_framework.get(framework, []))

        # Get metadata
        results = []
        for agent_id in agent_ids:
            metadata = self.get_metadata(agent_id)
            if metadata and (not enabled_only or metadata.enabled):
                results.append(metadata)

        return results

    def find_agents_by_capability(
            self,
            capability: AgentCapability,
            enabled_only: bool = True
    ) -> List[AgentMetadata]:
        """Find all agents with a specific capability."""
        return self.list_agents(capability=capability, enabled_only=enabled_only)

    def find_agents_by_business_unit(
            self,
            business_unit: str,
            enabled_only: bool = True
    ) -> List[AgentMetadata]:
        """Find all agents from a specific business unit."""
        return self.list_agents(business_unit=business_unit, enabled_only=enabled_only)

    def search_agents(self, query: str) -> List[AgentMetadata]:
        """
        Search agents by name, description, or tags.

        Args:
            query: Search term (case-insensitive)

        Returns:
            List of matching agent metadata
        """
        query_lower = query.lower()
        results = []

        for agent_id, agent_data in self._agents.items():
            metadata = agent_data["metadata"]

            # Search in name, description, and tags
            searchable_text = " ".join([
                metadata.name.lower(),
                metadata.description.lower(),
                " ".join(metadata.tags).lower()
            ])

            if query_lower in searchable_text:
                results.append(metadata)

        return results

    def execute_agent(
            self,
            agent_id: str,
            state: Dict[str, Any]
    ) -> AgentExecutionResult:
        """
        Execute an agent and return standardized result.

        Args:
            agent_id: ID of agent to execute
            state: Current state (input to agent)

        Returns:
            AgentExecutionResult with outputs or error
        """
        import time

        agent = self.get_agent(agent_id)
        if not agent:
            return AgentExecutionResult(
                agent_id=agent_id,
                success=False,
                outputs={},
                error=f"Agent {agent_id} not found",
                execution_time_seconds=0.0
            )

        metadata = agent["metadata"]
        executor = agent["executor"]

        # Check if agent is enabled
        if not metadata.enabled:
            return AgentExecutionResult(
                agent_id=agent_id,
                success=False,
                outputs={},
                error=f"Agent {agent_id} is disabled",
                execution_time_seconds=0.0
            )

        # Validate inputs
        missing_inputs = [
            key for key in metadata.required_inputs
            if key not in state
        ]
        if missing_inputs:
            return AgentExecutionResult(
                agent_id=agent_id,
                success=False,
                outputs={},
                error=f"Missing required inputs: {missing_inputs}",
                execution_time_seconds=0.0
            )

        # Execute
        start_time = time.time()
        try:
            self.logger.info(f"Executing agent: {agent_id}")
            outputs = executor(state)
            execution_time = time.time() - start_time

            self.logger.info(
                f"✓ Agent {agent_id} completed in {execution_time:.2f}s"
            )

            return AgentExecutionResult(
                agent_id=agent_id,
                success=True,
                outputs=outputs,
                execution_time_seconds=execution_time,
                metadata={
                    "agent_name": metadata.name,
                    "business_unit": metadata.business_unit
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"✗ Agent {agent_id} failed: {str(e)}")

            return AgentExecutionResult(
                agent_id=agent_id,
                success=False,
                outputs={},
                error=str(e),
                execution_time_seconds=execution_time
            )

    def update_agent(
            self,
            agent_id: str,
            metadata: Optional[AgentMetadata] = None,
            executor: Optional[Callable] = None
    ) -> None:
        """
        Update an existing agent.

        Args:
            agent_id: ID of agent to update
            metadata: New metadata (optional)
            executor: New executor (optional)
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        if metadata:
            # Clear old indexes
            old_metadata = self._agents[agent_id]["metadata"]
            for capability in old_metadata.capabilities:
                self._by_capability[capability].remove(agent_id)
            self._by_business_unit[old_metadata.business_unit].remove(agent_id)
            self._by_framework[old_metadata.framework].remove(agent_id)

            # Update and reindex
            self._agents[agent_id]["metadata"] = metadata
            for capability in metadata.capabilities:
                self._by_capability[capability].append(agent_id)
            self._by_business_unit[metadata.business_unit].append(agent_id)
            self._by_framework[metadata.framework].append(agent_id)

        if executor:
            self._agents[agent_id]["executor"] = executor

        self.logger.info(f"✓ Updated agent: {agent_id}")

    def unregister_agent(self, agent_id: str) -> None:
        """Remove agent from registry."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        # Remove from indexes
        metadata = self._agents[agent_id]["metadata"]
        for capability in metadata.capabilities:
            self._by_capability[capability].remove(agent_id)
        self._by_business_unit[metadata.business_unit].remove(agent_id)
        self._by_framework[metadata.framework].remove(agent_id)

        # Remove from main registry
        del self._agents[agent_id]

        self.logger.info(f"✓ Unregistered agent: {agent_id}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_agents": len(self._agents),
            "enabled_agents": len([
                a for a in self._agents.values()
                if a["metadata"].enabled
            ]),
            "by_framework": {
                framework.value: len(agents)
                for framework, agents in self._by_framework.items()
            },
            "by_business_unit": {
                unit: len(agents)
                for unit, agents in self._by_business_unit.items()
            },
            "by_capability": {
                capability.value: len(agents)
                for capability, agents in self._by_capability.items()
            }
        }

    def print_summary(self) -> None:
        """Print registry summary."""
        stats = self.get_statistics()

        print("=" * 70)
        print("AGENT REGISTRY SUMMARY")
        print("=" * 70)
        print(f"\nTotal Agents: {stats['total_agents']}")
        print(f"Enabled: {stats['enabled_agents']}")

        print(f"\nBy Framework:")
        for framework, count in stats['by_framework'].items():
            print(f"  {framework}: {count}")

        print(f"\nBy Business Unit:")
        for unit, count in stats['by_business_unit'].items():
            print(f"  {unit}: {count}")

        print(f"\nBy Capability:")
        for capability, count in stats['by_capability'].items():
            print(f"  {capability}: {count}")

        print("=" * 70)


# Global registry instance
_global_registry = None


def get_registry() -> AgentRegistry:
    """Get global agent registry (singleton)."""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


# Convenience decorators for easy registration
def register_agent(
        agent_id: str,
        name: str,
        description: str,
        framework: AgentFramework,
        capabilities: List[AgentCapability],
        business_unit: str,
        contact: str,
        **kwargs
):
    """
    Decorator to register an agent function.

    Usage:
        @register_agent(
            agent_id="my_agent",
            name="My Agent",
            description="Does something cool",
            framework=AgentFramework.CUSTOM,
            capabilities=[AgentCapability.RESEARCH],
            business_unit="my_team",
            contact="team@company.com"
        )
        def my_agent(state: Dict[str, Any]) -> Dict[str, Any]:
            # Agent logic
            return {"result": "success"}
    """

    def decorator(func: Callable) -> Callable:
        metadata = AgentMetadata(
            agent_id=agent_id,
            name=name,
            description=description,
            framework=framework,
            capabilities=capabilities,
            business_unit=business_unit,
            contact=contact,
            **kwargs
        )

        registry = get_registry()
        registry.register_agent(metadata, func)

        return func

    return decorator