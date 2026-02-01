from langgraph.graph import StateGraph, START, END
from src.nodes import verify, analyze, collect
from singleton_decorator import singleton
from src.models import State, Sample
from .kernel import Kernel

@singleton
class Agent:

    def __init__(self):

        self.workflow = StateGraph(State)

        # Nodes
        self.workflow.add_node('verify', verify.build_and_boot)
        self.workflow.add_node('analyze', analyze.analyze)
        self.workflow.add_node('collect', collect.collect)

        # Edges
        self.workflow.add_edge(START, 'verify')
        
        self.workflow.add_conditional_edges(
            'verify',
            verify.route,
            {
                'analyze': 'analyze',
                END: END,
            }
        )

        self.workflow.add_conditional_edges(
            'analyze',
            analyze.route,
            {
                'verify': 'verify',
                'collect': 'collect',
            }
        )

        self.workflow.add_conditional_edges(
            'collect',
            collect.route,
            {
                'analyze': 'analyze',
                'verify': 'verify',
            }
        )

        # Compile
        self.agent = self.workflow.compile()

    def repair(self, sample: Sample) -> dict:
        
        kernel = Kernel(sample.kernel_src)

        initial_state = State(
            patch=sample.patch,
            base_config=sample.base_config,
            sample_dir=sample.sample_dir,
            latest_config=sample.base_config,
            kernel=kernel,
        )

        final_state = self.agent.run(initial_state)

        return final_state.model_dump()

agent = Agent()