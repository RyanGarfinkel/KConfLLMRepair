from singleton_decorator import singleton
from langgraph.graph import END
from src.config import settings
from src.models import State

@singleton
class VerifyNode:

    def build_and_boot(self, state: State) -> dict:

        attempt_dir = f'{state.sample_dir}/attempt_{state.repair_attempts}'
        build_log = f'{attempt_dir}/build.log'

        hypotheses = state.hypotheses.copy()
        current_hypothesis = next((h for h in hypotheses if h.status == 'current'), None)

        if not state.kernel.build(state.latest_config, build_log):

            if current_hypothesis:
                current_hypothesis.status = 'failed'
            
            return {
                'repair_attempts': state.repair_attempts + 1,
                'latest_build': build_log,
                'boot_succeeded': False,
                'latest_boot': None,
                'hypotheses': hypotheses,
            }

        boot_log = f'{attempt_dir}/boot.log'
        boot_success = state.kernel.boot(boot_log)

        if current_hypothesis:
            current_hypothesis.status = 'success' if boot_success else 'failed'

        return {
            'repair_attempts': state.repair_attempts + 1,
            'boot_succeeded': boot_success,
            'latest_build': build_log,
            'latest_boot': boot_log,
            'hypotheses': hypotheses,
        }

    def route(self, state: State) -> str:

        if state.repair_attempts >= settings.agent.MAX_ITERATIONS:
            return END
        
        if state.boot_succeeded:
            return END
        
        return 'analyze'

verify = VerifyNode()
