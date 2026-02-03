from abc import ABC, abstractmethod
from langgraph.graph import END
from src.config import settings
from src.models import State

class Router(ABC):

    @abstractmethod
    def route(self, state: State) -> str:
        pass

    def check_thresholds(self, state: State) -> bool:
        
        if state.get('tool_calls') >= settings.agent.MAX_TOOL_CALLS:
            return False
        
        if state.get('verify_attempts') >= settings.agent.MAX_VERIFY_ATTEMPTS:
            return False
        
        return True
    
    def __call__(self, state: State) -> str:
        
        if not self.check_thresholds(state):
            return END
        
        return self.route(state)
