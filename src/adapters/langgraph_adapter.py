"""
LangGraph Agent Adapter

Wraps LangGraph graphs to work with our unified state system.
"""

from typing import Dict, Any, Optional
from src.adapters.base_adapter import BaseAgentAdapter


class LangGraphAgentAdapter(BaseAgentAdapter):
    """
    Adapter for LangGraph compiled graphs.

    Handles:
    - LangGraph CompiledGraph
    - LangGraph StateGraph
    """

    def __init__(
            self,
            agent: Any,
            config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize LangGraph adapter.

        Args:
            agent: LangGraph compiled graph
            config: Configuration including:
                - state_mapping: How to map our state to LangGraph state
                - output_mapping: How to extract outputs from LangGraph state
        """
        super().__init__(agent, config)

        self.state_mapping = self.config.get("state_mapping", {})
        self.output_mapping = self.config.get("output_mapping", {})

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LangGraph graph.

        Args:
            state: Current workflow state

        Returns:
            Dict with graph outputs
        """
        try:
            self.logger.info("Executing LangGraph agent")

            # Prepare input for LangGraph
            graph_input = self.preprocess(state)

            # Execute graph
            # LangGraph graphs use invoke() or stream()
            if hasattr(self.agent, "invoke"):
                result = self.agent.invoke(graph_input)
            else:
                # Fallback to direct call
                result = self.agent(graph_input)

            # Extract outputs
            output = self.postprocess(result)

            self.logger.info("LangGraph agent execution successful")
            return output

        except Exception as e:
            self.logger.error(f"LangGraph agent execution failed: {str(e)}")
            raise

    def preprocess(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map our state to LangGraph state format.

        Args:
            state: Our workflow state

        Returns:
            State in format expected by LangGraph
        """
        if not self.state_mapping:
            # No mapping specified, pass state as-is
            return state

        # Apply mapping
        graph_state = {}
        for our_key, graph_key in self.state_mapping.items():
            if our_key in state:
                graph_state[graph_key] = state[our_key]

        return graph_state

    def postprocess(self, agent_output: Any) -> Dict[str, Any]:
        """
        Extract outputs from LangGraph state.

        Args:
            agent_output: LangGraph state after execution

        Returns:
            Dict to merge into our workflow state
        """
        # LangGraph returns state dict
        if isinstance(agent_output, dict):
            if not self.output_mapping:
                # No mapping, return as-is
                return agent_output

            # Apply reverse mapping
            our_state = {}
            for graph_key, our_key in self.output_mapping.items():
                if graph_key in agent_output:
                    our_state[our_key] = agent_output[graph_key]

            return our_state

        # Fallback
        return {"langgraph_output": agent_output}

    def validate_inputs(self, state: Dict[str, Any]) -> bool:
        """Validate required inputs."""
        if self.state_mapping:
            # Check all mapped keys are present
            missing = [
                key for key in self.state_mapping.keys()
                if key not in state
            ]
            if missing:
                self.logger.error(f"Missing required inputs: {missing}")
                return False

        return True


def wrap_langgraph_agent(
        graph: Any,
        state_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[Dict[str, str]] = None,
        **kwargs
) -> LangGraphAgentAdapter:
    """
    Convenience function to wrap LangGraph graph.

    Args:
        graph: Compiled LangGraph graph
        state_mapping: Map our state keys to graph state keys
        output_mapping: Map graph output keys to our state keys

    Usage:
        from langgraph.graph import StateGraph

        # Build graph
        workflow = StateGraph(MyState)
        workflow.add_node("step1", step1_func)
        # ... add more nodes
        graph = workflow.compile()

        # Wrap for our system
        wrapped = wrap_langgraph_agent(
            graph,
            state_mapping={"input": "user_input"},
            output_mapping={"result": "output"}
        )

        # Register
        registry.register_agent(metadata, wrapped)
    """
    config = {
        "state_mapping": state_mapping or {},
        "output_mapping": output_mapping or {},
        **kwargs
    }
    return LangGraphAgentAdapter(graph, config)