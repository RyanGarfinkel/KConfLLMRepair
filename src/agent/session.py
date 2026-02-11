
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from src.models import Attempt, ToolCall, TokenUsage, AgentResponse
from src.tools import diffconfig
from src.utils import file_lock
from src.config import settings
from typing import Tuple
import shutil
import json
import os

class Session:
    
    def __init__(self, config: str, output: str):

        self.base = config
        self.attempts: list[Attempt] = []
        self.dir = output

    @property
    def latest(self) -> str | None:
        if len(self.attempts) == 0:
            return self.base
        
        return self.attempts[-1].config
    
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
    
    @property
    def edits(self) -> Tuple[list[str], int] | None:
        if self.status != 'Success' or not self.latest:
            return [], -1
        
        return diffconfig.diffconfig(self.base, self.latest)
    
    def add_attempt(self, messages: list[BaseMessage], response: AgentResponse | None = None):
        
        id = len(self.attempts)
        dir = f'{self.dir}/attempt_{id}'

        messages = self.__get_latest_messages(messages)
        tool_calls = self.__map_tool_calls(messages) if messages else []
        
        self.attempts.append(Attempt(
            id=id,
            dir=dir,
            tool_calls=tool_calls,
            response=response,
            klocalizer_succeeded=response is None,
        ))

        if messages is not None:
            ai_message = messages[0]
            self.attempts[-1].add_token_usage(
                input_tokens=ai_message.usage_metadata['input_tokens'] if ai_message.usage_metadata else 0,
                output_tokens=ai_message.usage_metadata['output_tokens'] if ai_message.usage_metadata else 0,
                total_tokens=ai_message.usage_metadata['total_tokens'] if ai_message.usage_metadata else 0
            )

        if os.path.exists(dir):
            shutil.rmtree(dir)

        os.makedirs(dir, exist_ok=True)

    def __get_latest_messages(self, messages: list[BaseMessage]) -> list[BaseMessage] | None:

        index = len(messages) - 1
        while index >= 0 and not isinstance(messages[index], AIMessage):
            index -= 1

        return messages[index:] if index >= 0 else None

    def __map_tool_calls(self, messages: list[BaseMessage]) -> list[ToolCall]:

        ai_message = messages[0] if messages and isinstance(messages[0], AIMessage) else None
        tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]

        tool_map = {tool.name: tool for tool in tool_messages}

        tool_calls = []
        if ai_message is not None:
            self.attempts[-1].add_token_usage(
                input_tokens=ai_message.usage_metadata['input_tokens'] if ai_message.usage_metadata else 0,
                output_tokens=ai_message.usage_metadata['output_tokens'] if ai_message.usage_metadata else 0,
                total_tokens=ai_message.usage_metadata['total_tokens'] if ai_message.usage_metadata else 0
            )
            for tool_call in ai_message.tool_calls:

                tool = tool_map.get(tool_call['name'])
                if not tool:
                    continue

                tool_calls.append(ToolCall(
                    name=tool_call['name'],
                    args=tool_call['args'],
                    response=tool.content
                ))

        return tool_calls
    
    def save(self, path: str):
        with file_lock:
            with open(path, 'w') as f:
                json.dump(self.__dict__(), f, indent=4)
    
    def __dict__(self) -> dict:
        token_usage = TokenUsage(
            input_tokens=sum(attempt.token_usage.input_tokens for attempt in self.attempts),
            output_tokens=sum(attempt.token_usage.output_tokens for attempt in self.attempts),
            total_tokens=sum(attempt.token_usage.total_tokens for attempt in self.attempts)
        )

        edits, edit_distance = self.edits
        
        return {
            'summary': {
                'status': self.status,
                'attempts': len(self.attempts) - 1,
                'original_config': self.base,
                'repaired_config': self.attempts[-1].config if self.status == 'Success' else None,
                'edit_distance': edit_distance
            },
            'token_usage': token_usage.model_dump(),
            'attempts': [attempt.model_dump() for attempt in self.attempts],
            'edits': edits
        }
