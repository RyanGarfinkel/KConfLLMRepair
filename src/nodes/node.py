from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from abc import ABC, abstractmethod
from src.config import settings
from src.models import State
from typing import Literal

class Node(ABC):

    def __init__(self, llm: BaseChatModel, name: Literal['verify', 'analyze', 'collect', 'tool']):
        self.llm = llm
        self.name = name
        self.system_message = SystemMessage(content="""
            You are an expert Linux Kernel Engineer who specializes in boot repairs. The current configuration you are working on does
            not boot successfully. It was recently modified with the klocalizer tool to include code changes from a patch file. We want
            to include these code chnages so syzkaller can test them, but first we need to get the kernel to boot successfully. Your task
            is to analyze the klocalizer, build, and boot logs, form a hypothesis, collect information from the original and latest configuration
            files, and guide klocalizer to make the necessary configuration changes to get the kernel to boot successfully.
        """)

    @property
    @abstractmethod
    def state_message(self) -> SystemMessage:
        pass

    def tools(self, state: State):
        return []

    @abstractmethod
    def _handle_response(self, response: AIMessage, state: State) -> dict:
        pass

    def __call__(self, state: State) -> dict:

        # Agent Setup
        agent = self.llm.bind_tools(self.tools(state))
        prompt = [self.system_message, self.state_message] + state.get('messages')[-settings.agent.MESSAGE_LENGTH:]

        # Agent Execution & Response Handling
        response = agent.invoke(prompt)
        result = self._handle_response(response, state)

        return result
