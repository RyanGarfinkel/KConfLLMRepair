from src.routers import verify_router, analyze_router, collect_router
from src.nodes import VerifyNode, AnalyzeNode, CollectNode
from langgraph.graph import StateGraph, START 
from src.llm import model, Session, Callback
from singleton_decorator import singleton
from src.models import State, Input
from .kernel import Kernel

@singleton
class Agent:
    
    def __init__(self):
        self.workflow = StateGraph(State)
        self.llm = model.get()

    def repair(self, input: Input, kernel: Kernel) -> tuple[dict, Session]:
        # Nodes
        self.workflow.add_node('verify', VerifyNode(kernel), tags=['verify'])
        self.workflow.add_node('analyze', AnalyzeNode(self.llm), tags=['analyze'])
        self.workflow.add_node('collect', CollectNode(self.llm, kernel), tags=['collect'])

        # Edges
        self.workflow.add_edge(START, 'verify')
        self.workflow.add_conditional_edges('verify', verify_router)
        self.workflow.add_conditional_edges('analyze', analyze_router)
        self.workflow.add_conditional_edges('collect', collect_router)

        # Compile
        agent = self.workflow.compile()

        # State & Callback
        initial_state = State(
            messages=[],
            hypothesis=None,
            tool_calls=0,
            klocalizer_runs=0,
            verify_attempts=0,
            klocalizer_succeeded=False,
            verify_succeeded=False,
            base_config=input.base_config,
            modified_config=input.modified_config,
            patch=input.patch,
            build_log=None,
            boot_log=None,
            klocalizer_log=None,
            output_dir=input.output_dir
        )

        session = Session()
        callback = Callback(session)
        
        # Run
        final_state = agent.invoke(initial_state, config={'callbacks': [callback]})

        return final_state, session

agent = Agent()
