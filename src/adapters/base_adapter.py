"""
Base Adapter Interface

Defines the contract for wrapping agents from different frameworks.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging


class BaseAgentAdapter(ABC):
    """Abstract base class for agent adapters."""
    
    def __init__(self, agent: Any, config: Optional[Dict[str, Any]] = None):
        self.agent = agent
        self.config = config or {}
        self.logger = self._create_logger()
    
    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with given state."""
        pass
    
    @abstractmethod
    def validate_inputs(self, state: Dict[str, Any]) -> bool:
        """Validate that state contains required inputs."""
        pass
    
    def get_required_inputs(self) -> list:
        return self.config.get("required_inputs", [])
    
    def get_output_keys(self) -> list:
        return self.config.get("output_keys", [])
    
    def preprocess(self, state: Dict[str, Any]) -> Any:
        return state
    
    def postprocess(self, agent_output: Any) -> Dict[str, Any]:
        if isinstance(agent_output, dict):
            return agent_output
        return {"output": agent_output}
    
    def _create_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"Adapter-{self.__class__.__name__}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute(state)


class CustomAgentAdapter(BaseAgentAdapter):
    """Adapter for custom Python functions."""
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.logger.info("Executing custom agent")
            result = self.agent(state)
            
            if not isinstance(result, dict):
                self.logger.warning(
                    f"Agent returned {type(result)}, converting to dict"
                )
                result = self.postprocess(result)
            
            return result
        except Exception as e:
            self.logger.error(f"Custom agent execution failed: {str(e)}")
            raise
    
    def validate_inputs(self, state: Dict[str, Any]) -> bool:
        required = self.get_required_inputs()
        missing = [key for key in required if key not in state]
        
        if missing:
            self.logger.error(f"Missing required inputs: {missing}")
            return False
        
        return True


class PassthroughAdapter(BaseAgentAdapter):
    """Simple passthrough adapter."""
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return self.agent(state)
    
    def validate_inputs(self, state: Dict[str, Any]) -> bool:
        return True


def create_adapter(
    agent: Any,
    adapter_type: str = "custom",
    config: Optional[Dict[str, Any]] = None
) -> BaseAgentAdapter:
    """Factory function to create appropriate adapter."""
    adapters = {
        "custom": CustomAgentAdapter,
        "passthrough": PassthroughAdapter,
    }
    
    if adapter_type == "langchain":
        from src.adapters.langchain_adapter import LangChainAgentAdapter
        adapters["langchain"] = LangChainAgentAdapter
    
    if adapter_type == "langgraph":
        from src.adapters.langgraph_adapter import LangGraphAgentAdapter
        adapters["langgraph"] = LangGraphAgentAdapter
    
    adapter_class = adapters.get(adapter_type)
    if not adapter_class:
        raise ValueError(
            f"Unknown adapter type: {adapter_type}. "
            f"Available: {list(adapters.keys())}"
        )
    
    return adapter_class(agent, config)
