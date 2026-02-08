from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.language_models import BaseChatModel
from src.toolkit import analyze_tools
from functools import cached_property
from src.config import settings
from src.models import State
from .node import Node

class AnalyzeNode(Node):

    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, 'analyze')

    @cached_property
    def state_message(self) -> SystemMessage:
        return SystemMessage(content=
            """
                You are currently in the analyze phase of the kernel boot repair process. Your goal in this phase is to form a hypothesis
                about why the kernel is failing to boot successfully after the recent configuration changes made by klocalizer. You are
                able to analyze the klocalizer log, build log, and QEMU boot log using the provided tools to gather evidence to form your
                hypothesis. Once you have formed a hypothesis, you will express it using the express_hypothesis tool. It is encouraged that
                you first gather sufficient evidence before expressing your hypothesis to ensure its accuracy. Do not call the express_hypothesis
                tool until you have queried the logs. Only call the express_hypothesis tool once per analyze phase. The klocalizer log does not exist
                on the first analyze phase since klocalizer has not been run yet, so focus on analyzing the build and boot logs for the first hypothesis.
                After the first time klocalizer runs, you will have access to see it.
            """)
    
    def tools(self, state: State):
        return analyze_tools(state.get('patch'), state.get('klocalizer_log'), state.get('build_log'), state.get('boot_log'))
    
    def tool_map(self, state: State):
        return {tool.name: tool for tool in self.tools(state)}
    
    def _handle_response(self, response: AIMessage, state: State) -> dict:
        
        new_messages = [response]

        tool_count = state.get('tool_calls', 0)
        hypothesis = None
        tool_map = self.tool_map(state)

        for tool in response.tool_calls:

            if tool_count >= settings.agent.MAX_TOOL_CALLS:
                break

            name = tool['name']
            args = tool.get('args', {})

            if name not in tool_map:
                new_messages.append(ToolMessage(
                    tool_call_id=tool['id'],
                    name=name,
                    content=f'ERROR: Tool {name} not found. This call is skipped.'
                ))
                continue

            new_messages.append(ToolMessage(
                tool_call_id=tool['id'],
                name=name,
                content=tool_map[name].invoke(args)
            ))

            if name == 'express_hypothesis':
                hypothesis = new_messages[-1].content

            tool_count += 1


        return {
            'messages': new_messages,
            'hypothesis': hypothesis,
            'tool_calls': tool_count,
            'klocalizer_runs': 0,
            'verify_succeeded': False,
            'klocalizer_succeeded': False,
            'output_dir': state.get('output_dir')
        }
