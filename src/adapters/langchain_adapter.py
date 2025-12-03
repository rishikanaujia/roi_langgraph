"""
LangChain Agent Adapter

Wraps LangChain agents to work with our unified state system.
"""

from typing import Dict, Any, Optional
from src.adapters.base_adapter import BaseAgentAdapter


class LangChainAgentAdapter(BaseAgentAdapter):
    """
    Adapter for LangChain agents.
    
    Handles:
    - LangChain Agent executors
    - LangChain Chains
    - LangChain Runnables
    """
    
    def __init__(
        self,
        agent: Any,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize LangChain adapter.
        
        Args:
            agent: LangChain agent/chain/runnable
            config: Configuration including:
                - input_key: Key to extract from state for agent input
                - output_key: Key to store agent output in state
                - langchain_type: "agent" | "chain" | "runnable"
        """
        super().__init__(agent, config)
        
        self.input_key = self.config.get("input_key", "input")
        self.output_key = self.config.get("output_key", "output")
        self.langchain_type = self.config.get("langchain_type", "auto")
        
        # Auto-detect LangChain type if not specified
        if self.langchain_type == "auto":
            self.langchain_type = self._detect_langchain_type()
    
    def _detect_langchain_type(self) -> str:
        """Auto-detect the type of LangChain object."""
        agent_type_name = type(self.agent).__name__
        
        if "Agent" in agent_type_name:
            return "agent"
        elif "Chain" in agent_type_name:
            return "chain"
        elif "Runnable" in agent_type_name or hasattr(self.agent, "invoke"):
            return "runnable"
        else:
            self.logger.warning(
                f"Could not auto-detect LangChain type for {agent_type_name}, "
                f"assuming 'runnable'"
            )
            return "runnable"
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LangChain agent.
        
        Args:
            state: Current workflow state
        
        Returns:
            Dict with agent outputs
        """
        try:
            self.logger.info(
                f"Executing LangChain {self.langchain_type} agent"
            )
            
            # Extract input
            agent_input = self.preprocess(state)
            
            # Execute based on type
            if self.langchain_type == "agent":
                # LangChain agents typically use invoke() or run()
                if hasattr(self.agent, "invoke"):
                    result = self.agent.invoke(agent_input)
                else:
                    result = self.agent.run(agent_input)
            
            elif self.langchain_type == "chain":
                # Chains use invoke() or __call__
                if hasattr(self.agent, "invoke"):
                    result = self.agent.invoke(agent_input)
                else:
                    result = self.agent(agent_input)
            
            elif self.langchain_type == "runnable":
                # Runnables use invoke()
                result = self.agent.invoke(agent_input)
            
            else:
                raise ValueError(f"Unknown LangChain type: {self.langchain_type}")
            
            # Convert result to dict
            output = self.postprocess(result)
            
            self.logger.info("LangChain agent execution successful")
            return output
        
        except Exception as e:
            self.logger.error(f"LangChain agent execution failed: {str(e)}")
            raise
    
    def preprocess(self, state: Dict[str, Any]) -> Any:
        """
        Extract input for LangChain agent.
        
        Args:
            state: Current workflow state
        
        Returns:
            Input in format expected by LangChain agent
        """
        # If input_key specified, extract that specific value
        if self.input_key and self.input_key in state:
            return state[self.input_key]
        
        # Otherwise, pass entire state
        return state
    
    def postprocess(self, agent_output: Any) -> Dict[str, Any]:
        """
        Convert LangChain output to dict.
        
        Args:
            agent_output: Raw output from LangChain agent
        
        Returns:
            Dict to merge into state
        """
        # If output is already a dict, return it
        if isinstance(agent_output, dict):
            return agent_output
        
        # If output has dict-like attributes, convert
        if hasattr(agent_output, "__dict__"):
            return agent_output.__dict__
        
        # Otherwise, wrap in output_key
        return {self.output_key: agent_output}
    
    def validate_inputs(self, state: Dict[str, Any]) -> bool:
        """Validate required inputs."""
        if self.input_key and self.input_key not in state:
            self.logger.error(f"Missing required input key: {self.input_key}")
            return False
        
        return True


# Convenience function
def wrap_langchain_agent(
    agent: Any,
    input_key: str = "input",
    output_key: str = "output",
    **kwargs
) -> LangChainAgentAdapter:
    """
    Convenience function to wrap LangChain agent.
    
    Usage:
        from langchain.agents import AgentExecutor
        
        langchain_agent = AgentExecutor(...)
        wrapped = wrap_langchain_agent(
            langchain_agent,
            input_key="query",
            output_key="result"
        )
        
        # Now use in registry
        registry.register_agent(metadata, wrapped)
    """
    config = {
        "input_key": input_key,
        "output_key": output_key,
        **kwargs
    }
    return LangChainAgentAdapter(agent, config)
