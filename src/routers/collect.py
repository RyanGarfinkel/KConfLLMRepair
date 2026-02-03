from singleton_decorator import singleton
from src.config import settings
from src.models import State
from .router import Router

@singleton
class CollectRouter(Router):

    def route(self, state: State) -> str:

        if state.get('klocalizer_succeeded'):
            return 'verify'
        
        if not state.get('hypothesis') or state.get('klocalizer_runs') >= settings.agent.MAX_KLOCALIZER_RUNS:
            return 'analyze'
        
        return 'collect'

collect_router = CollectRouter()
