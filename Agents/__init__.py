# Agents/__init__.py
from .BaseAgent import BaseAgent
from .SingleAgent import SmartTutor
from .client import AzureOpenAIClient
from .TwoAgents import TwoAgentSystem, TutorAgent, CorrectorAgent

__all__ = [
    'BaseAgent',
    'SmartTutor',
    'AzureOpenAIClient',
    'TwoAgentSystem',
    'TutorAgent',
    'CorrectorAgent',
    'GeneratorAgent'
]