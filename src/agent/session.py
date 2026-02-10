
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from src.models import Attempt, ToolCall, TokenUsage, AgentResponse
from src.config import settings
import json
import os

class Session:
    
    def __init__(self, base: str, latest: str | None, patch: str | None, dir: str):

        self.base = base
        self.latest = latest if latest else base
        self.patch = patch
        self.attempts: list[Attempt] = []
        self.dir = dir

    @property
    def status(self) -> str:

        attempts = len(self.attempts)

        if attempts == 0:
            return 'Initialized'
        
        if self.attempts[-1].boot_succeeded:
            return 'Success'
        elif attempts >= settings.agent.MAX_ITERATIONS:
            return 'Max Attempts Reached'
        
        return 'In Progress'
    
    def add_attempt(self, messages: list[BaseMessage], response: AgentResponse | None = None):

        ai_message = next((msg for msg in messages if isinstance(msg, AIMessage)), None)
        tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]

        tool_map = {tool.name: tool for tool in tool_messages}

        tool_calls = []
        if ai_message is not None:
            for tool_call in ai_message.tool_calls:

                tool = tool_map.get(tool_call.name)
                if not tool:
                    continue

                tool_calls.append(ToolCall(
                    name=tool_call.name,
                    args=tool_call.args,
                    response=tool.response,
                    token_usage=TokenUsage(
                        input_tokens=tool.token_usage.input_tokens,
                        output_tokens=tool.token_usage.output_tokens,
                        total_tokens=tool.token_usage.total_tokens
                    )
                ))

        self.attempts.append(Attempt(
            id=len(self.attempts),
            dir=f'{self.dir}/attempt_{len(self.attempts)}',
            tool_calls=tool_calls,
            response=response,
            klocalizer_succeeded=response is None,
        ))

        if not os.path.exists(self.attempts[-1].dir):
            os.makedirs(self.attempts[-1].dir)

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.__dict__(), f, indent=4)
    
    def __dict__(self) -> dict:
        return {
            'summary': {
                'status': self.status,
                'attempts': len(self.attempts) - 1,
                'base': self.base,
                'patch': self.patch,
                'repaired_config': self.attempts[-1].config if self.status == 'Success' else None,
            },
            'attempts': [attempt.model_dump() for attempt in self.attempts]
        }
