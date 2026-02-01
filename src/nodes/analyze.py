from langchain_core.messages import SystemMessage
from singleton_decorator import singleton
from src.models import State, Hypothesis
from .tool import analyze_tools
from .node import Node

from functools import cached_property

@singleton
class AnalyzeNode(Node):

    def __init__(self):
        super().__init__('analyze')

    @cached_property
    def state_message(self) -> SystemMessage:
        return SystemMessage(content=
            """
                You are currently in the analyze phase of the kernel boot repair process. Your goal in this phase is to form a hypothesis
                about why the kernel is failing to boot successfully after the recent configuration changes made by klocalizer. You are
                able to analyze the klocalizer log, build log, and QEMU boot log using the provided tools to gather evidence to form your
                hypothesis. Once you have formed a hypothesis, you will express it using the express_hypothesis tool.                                               
            """)
    
    def _handle_response(self, response, state):
        
        pass

    def analyze(self, state: State) -> dict:
        
        # Agent Setup
        tools = analyze_tools
        tool_map = {tool.name: tool for tool in tools}

        agent = self.llm.bind_tools(tools)

        # Execute Agent and Tool Calls
        response = agent.invoke(self._get_prompt(self.state_message, state.messages))
        new_messages = [response]

        if response.tool_calls:
            for call in response.tool_calls:
                new_messages.append(self._execute_tool(call, tool_map))

        # Check Hypothesis
        expressed_hypothesis = next((call for call in response.tool_calls if call['name'] == 'express_hypothesis'), None)
        hypotheses = state.hypotheses.copy()

        if expressed_hypothesis:
            hypothesis = Hypothesis(text=expressed_hypothesis['args']['hypothesis'], status='current')
            hypotheses.append(hypothesis)

        return {
            'messages': new_messages,
            'hypotheses': hypotheses,
        }
    
    def router(self, state: State) -> str:

        if state.current_hypothesis is not None:
            return 'collect'
        
        return 'analyze'
    
analyze = AnalyzeNode()
