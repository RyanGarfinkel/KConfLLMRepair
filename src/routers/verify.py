from singleton_decorator import singleton
from langgraph.graph import END
from src.models import State
from .router import Router

@singleton
class VerifyRouter(Router):

    def route(self, state: State) -> str:

        if state.get('verify_succeeded'):
            return END
        
        return 'analyze'
    
verify_router = VerifyRouter()
