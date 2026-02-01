from langchain_core.messages import SystemMessage, AIMessage
from langchain.core.runnable import RunnableConfig
from .tool import analyze_tools, collect_tools
from abc import ABC, abstractmethod
from src.config import settings
from src.models import State
from typing import Literal
from typing import final

class Node(ABC):

    def __init__(self, name: Literal['verify', 'analyze', 'collect', 'tool']):
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

    @abstractmethod
    def _handle_response(self, response: AIMessage, state: State) -> dict:
        pass

    @abstractmethod
    def router(self, state: State) -> str:
        pass

    @final
    def __call__(self, state: State, config: RunnableConfig) -> dict:

        # Agent Setup
        if self.name == 'analyze':
            agent = settings.agent.LLM.bind_tools(analyze_tools)
        elif self.name == 'collect':
            agent = settings.agent.LLM.bind_tools(collect_tools)
        else:
            agent = settings.agent.LLM

        prompt = [self.system_message, self.state_message] + state.get('messages')[-settings.agent.MAX_CONTENT_MESSAGES:]

        # Agent Execution & Response Handling
        response = agent.invoke(prompt)
        
        result = self._handle_response(response, state, config)

        return result
