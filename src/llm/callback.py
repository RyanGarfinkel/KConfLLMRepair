from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, messages_to_dict
from langchain_core.callbacks import BaseCallbackHandler
from src.utils import file_lock
from typing import List, cast
from src.models import State
from .session import Session
import json
import os

class Callback(BaseCallbackHandler):

    def __init__(self, session: Session):
        self.session = session

    def on_chain_start(self, serialized, inputs, **kwargs):
        node = kwargs.get('name', '')
        current = self.session.current_phase.name if self.session.current_phase else 'None'
        
        if node == 'verify' and current != 'verify':
            self.session.start_phase('verify')
        elif node == 'analyze' and current != 'analyze':
            self.session.start_phase('analyze')
        elif node == 'collect' and current != 'collect':
            self.session.start_phase('collect')
    
    def on_chain_end(self, outputs, **kwargs):
        if not self.session.current_phase or not any(t.startswith('graph:step') for t in kwargs.get('tags', [])):
            return

        messages = outputs.get('messages', [])
        output_dir = outputs.get('output_dir', '')

        message_file = f'{output_dir}/messages.json'
        summary_file = f'{output_dir}/summary.json'

        if self.session.current_phase.name == 'verify':
            self.handle_verify_end(messages[-1].content, outputs.get('verify_attempts', 1), output_dir)
            self.log_messages(messages, message_file)
            self.log_session(summary_file, outputs)
            return
        
        ai_message = next((m for m in messages if isinstance(m, AIMessage)), None)
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]

        if not ai_message:
            return
        
        # Record Token Usage
        usage = ai_message.usage_metadata
        if usage is not None:
            self.session.current_phase.add_token_usage(usage.get('input_tokens', 0), usage.get('output_tokens', 0))

        # Match Tool Calls
        map = { msg.tool_call_id: msg for msg in tool_messages }
        for tool_call in ai_message.tool_calls:
            response = map.get(tool_call['id'])
            self.session.current_phase.add_tool_action(
                name=tool_call['name'],
                args=tool_call['args'],
                response=response.content if response else ''
            )

        self.log_messages(messages, message_file)
        self.log_session(summary_file, outputs)

    def handle_verify_end(self, response: str, verify_attempts: int, output_dir: str):

        attempt_dir = f'{output_dir}/attempt_{verify_attempts - 1}'
        if response.startswith('ERROR: Build'):
            self.session.current_phase.add_verify_action(
                build_succeeded=False,
                build_log=f'{attempt_dir}/build.log',
                boot_succeeded=False,
                boot_log=None
            )
        elif response.startswith('ERROR: Boot'):
            self.session.current_phase.add_verify_action(
                build_succeeded=True,
                build_log=f'{attempt_dir}/build.log',
                boot_succeeded=False,
                boot_log=f'{attempt_dir}/boot.log'
            )
        elif response.startswith('SUCCESS'):
            self.session.current_phase.add_verify_action(
                build_succeeded=True,
                build_log=f'{attempt_dir}/build.log',
                boot_succeeded=True,
                boot_log=f'{attempt_dir}/boot.log'
            )
        else:
            self.session.current_phase.add_verify_action(
                build_succeeded=False,
                build_log=None,
                boot_succeeded=False,
                boot_log=None
            )
   
    def log_session(self, file: str, state: dict):
        with file_lock:
            with open(file, 'w') as f:
                json.dump(self.session.model_dump(cast(State, state)), f, indent=4)

    def log_messages(self, messages: List[BaseMessage], file: str):
        with file_lock:
            with open(file, 'w') as f:
                json.dump(messages_to_dict(messages), f, indent=4)