"""
Agent Adapters Package

Adapters for normalizing different agent frameworks.
"""

# Note: Import adapters lazily to avoid circular imports
# and missing dependencies

__all__ = [
    'BaseAgentAdapter',
    'CustomAgentAdapter',
    'PassthroughAdapter',
    'LangChainAgentAdapter',
    'create_adapter'
]

# Lazy imports - only import when explicitly requested
def __getattr__(name):
    if name == 'BaseAgentAdapter':
        from src.adapters.base_adapter import BaseAgentAdapter
        return BaseAgentAdapter
    elif name == 'CustomAgentAdapter':
        from src.adapters.base_adapter import CustomAgentAdapter
        return CustomAgentAdapter
    elif name == 'PassthroughAdapter':
        from src.adapters.base_adapter import PassthroughAdapter
        return PassthroughAdapter
    elif name == 'LangChainAgentAdapter':
        from src.adapters.langchain_adapter import LangChainAgentAdapter
        return LangChainAgentAdapter
    elif name == 'create_adapter':
        from src.adapters.base_adapter import create_adapter
        return create_adapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
