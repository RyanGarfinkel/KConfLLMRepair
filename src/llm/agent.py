from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from src.utils.signature import extract_boot_signature
from src.llm.prompt import system_prompt
import json

class Agent:

    def __init__(self, dir, tools):

        self.model = ChatOpenAI(model='gpt-4o-mini')

        self.tools = tools
        self.dir = dir

        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
        )

    def repair(self):
        
        signatures = extract_boot_signature(f'{self.dir}/try_0/qemu.log')
        if signatures and len(signatures) > 0:
            input = f"The kernel failed to boot with panic signatures: {', '.join(signatures)}"
        else:
            input = "The kernel failed to boot. Please analyze the qemu log to determine the cause."

        result = self.agent.invoke({
            'messages': [
                ('system', system_prompt),
                ('user', input),
            ]
        })

        print(f'Agent output: {result}')
        with open(f'{self.dir}/result.json', 'w') as f:
            json.dump(self._extract_result_info(result), f, indent=4)

        output = result.get('output', '').lower()
        success = 'successfully' in output or 'you may stop now' in output

        return success

    def _extract_result_info(self, result):
        """Extract key information from the agent result."""
        # Get output from the result dict or fallback to the last message content
        output = result.get('output', '')
        if not output and 'messages' in result and len(result['messages']) > 0:
            last_msg = result['messages'][-1]
            output = getattr(last_msg, 'content', str(last_msg))

        info = {
            'output': output,
            'total_tokens': 0,
            'model_name': '',
            'model_provider': '',
            'tool_used': False
        }
        
        # Find the last AI message for metadata
        for msg in reversed(result.get('messages', [])):
            if msg.__class__.__name__ == 'AIMessage':
                if hasattr(msg, 'response_metadata') and msg.response_metadata:
                    metadata = msg.response_metadata
                    info['model_provider'] = metadata.get('model_provider', '')
                    info['model_name'] = metadata.get('model_name', '')
                
                if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                    usage = msg.usage_metadata
                    info['total_tokens'] = usage.get('total_tokens', 0)
                
                # Check if this message used tools
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    info['tool_used'] = True
                
                break  # We only need the last AI message
        
        # Also check if any message in the conversation used tools
        for msg in result.get('messages', []):
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                info['tool_used'] = True
                break
        
        return info