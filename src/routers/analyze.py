from singleton_decorator import singleton
from src.models import State
from .router import Router

@singleton
class AnalyzeRouter(Router):

    def route(self, state: State) -> str:

        if state.get('hypothesis'):
            return 'collect'
        
        return 'analyze'

analyze_router = AnalyzeRouter()
