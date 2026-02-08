from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from src.toolkit import collect_tools
from functools import cached_property
from src.config import settings
from src.models import State
from src.core import Kernel
from .node import Node
import shutil
import os

class CollectNode(Node):

    def __init__(self, llm: BaseChatModel, kernel: Kernel):
        super().__init__(llm, 'collect')
        self.kernel = kernel
    
    @cached_property
    def state_message(self) -> SystemMessage:
        return SystemMessage(content=
            """
                You are currently in the collect phase of the kernel boot repair process. Your goal in this phase is to gather information
                from the original, bootable, configuration and the latest, non-bootable, configuration to either confirm or refute the current
                hypothesis. When you have sufficient evidence to support your hypothesis, run the kloclaizer tool and specify which options
                to define and undefine. If you do not have sufficient evidence, you may discard your current hypothesis and return to the analyze
                phase. Do not run the klocalizer tool and the discard_hypothesis tool in the same response. You may only run klocizer once per
                response and will have a few chances to get it right before needing to return to the analyze phase. If klocalizer succeeds, you
                will move directly to the verify phase.                                          
            """)
    
    def tools(self, state: State):
        return collect_tools(state.get('base_config'), state.get('modified_config'), state.get('patch'), self.kernel)

    def tool_map(self, state: State):
        return {tool.name: tool for tool in self.tools(state)}
    
    def _handle_response(self, response: AIMessage, state: State) -> dict:
        
        new_messages = [response]

        tool_count = state.get('tool_calls', 0)
        modified_config = state.get('modified_config')
        klocalizer_log = state.get('klocalizer_log')
        klocalizer_runs = state.get('klocalizer_runs', 0)
        hypothesis = state.get('hypothesis')
        
        search_calls = [call for call in response.tool_calls if call['name'].startswith('search_')]
        klocalizer_calls = [call for call in response.tool_calls if call['name'] == 'run_klocalizer']
        hypothesis_calls = [call for call in response.tool_calls if call['name'] == 'discard_hypothesis']

        tool_map = self.tool_map(state)

        for call in search_calls:

            if tool_count >= settings.agent.MAX_TOOL_CALLS:
                break

            name = call['name']
            args = call.get('args', {})

            if name not in tool_map:
                new_messages.append(ToolMessage(
                    tool_call_id=call['id'],
                    name=name,
                    content=f'ERROR: Tool {name} not found. This call is skipped.'
                ))
                continue

            new_messages.append(ToolMessage(
                tool_call_id=call['id'],
                name=name,
                content=tool_map[name].invoke(args)
            ))

            tool_count += 1
        
        klocalizer_succeeded = False
        attempt_dir = f'{state.get('output_dir')}/attempt_{state.get('verify_attempts', 0)}'  
        for call in klocalizer_calls:

            if tool_count >= settings.agent.MAX_TOOL_CALLS:
                break

            name = call['name']
            args = call.get('args', {})

            if klocalizer_runs >= settings.agent.MAX_KLOCALIZER_RUNS:
                new_messages.append(ToolMessage(
                    tool_call_id=call['id'],
                    name=name,
                    content='ERROR: Maximum number of KLocalizer runs reached during this collect phase. This call is skipped.'
                ))
            elif klocalizer_succeeded:
                new_messages.append(ToolMessage(
                    tool_call_id=call['id'],
                    name=name,
                    content='Klocalizer already succeeded in a previous call. This call is skipped.'
                ))
            else:
                klocalizer_runs += 1
                
                os.makedirs(attempt_dir, exist_ok=True)

                new_messages.append(ToolMessage(
                    tool_call_id=call['id'],
                    name=name,
                    content=tool_map[name].invoke(args)
                ))

                attempts = 0
                while(os.path.exists(f'{attempt_dir}/klocalizer_{attempts}.log')):
                    attempts += 1

                if os.path.exists(f'{self.kernel.src}/klocalizer.log'): 
                    shutil.move(f'{self.kernel.src}/klocalizer.log', f'{attempt_dir}/klocalizer_{attempts}.log')
                    klocalizer_log = f'{attempt_dir}/klocalizer_{attempts}.log'


                if new_messages[-1].content.startswith('SUCCESS'):
                    klocalizer_succeeded = True
                    modified_config = f'{attempt_dir}/modified_config_{attempts}.config'
                    shutil.copyfile(f'{self.kernel.src}/.config', modified_config)
            
            tool_count += 1

        if len(hypothesis_calls) > 0:
            hypothesis = None

        for call in hypothesis_calls:
            
            if tool_count >= settings.agent.MAX_TOOL_CALLS:
                break
            
            new_messages.append(ToolMessage(
                tool_call_id=hypothesis_calls[0]['id'],
                name='discard_hypothesis',
                content='Hypothesis discarded.'
            ))

            tool_count += 1

        return {
            'messages': new_messages,
            'hypothesis': hypothesis,
            'tool_calls': tool_count,
            'klocalizer_runs': klocalizer_runs,
            'klocalizer_succeeded': klocalizer_succeeded,
            'modified_config': modified_config,
            'klocalizer_log': klocalizer_log,
            'output_dir': state.get('output_dir'),
        }
