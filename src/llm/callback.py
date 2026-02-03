from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.callbacks import BaseCallbackHandler
from .session import Session

class Callback(BaseCallbackHandler):

    def __init__(self, session: Session):
        self.session = session

    def on_chain_start(self, serialized, inputs, **kwargs):
        tags = kwargs.get('tags', [])
        
        if 'verify' in tags:
            self.session.start_phase('verify')
        elif 'analyze' in tags:
            self.session.start_phase('analyze')
        elif 'collect' in tags:
            self.session.start_phase('collect')
    
    def on_chain_end(self, outputs, **kwargs):
        if not self.session.current_phase:
            return
            
        messages = outputs.get('messages', [])
        
        if self.session.current_phase.name == 'verify':
            self.handle_verify_end(messages[-1].content, outputs.get('verify_attempts', 1), outputs.get('output_dir', ''))
            return
        
        ai_message = next((m for m in messages if isinstance(m, AIMessage)), None)
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]

        if not ai_message:
            return
        
        # Record Token Usage
        usage = ai_message.usage_metadata
        if usage is not None:
            self.session.current_phase.add_token_usage(usage.input_tokens, usage.output_tokens)

        # Match Tool Calls
        map = { msg.tool_call_id: msg for msg in tool_messages }
        for tool_call in ai_message.tool_calls:
            response = map.get(tool_call['id'])
            self.session.current_phase.add_tool_action(
                name=tool_call['name'],
                args=tool_call['args'],
                response=response.content if response else ''
            )

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
   