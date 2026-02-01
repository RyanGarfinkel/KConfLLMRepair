from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from singleton_decorator import singleton
from langchain.tools import tool
from .node import Node
import os

@singleton
class CollectNode(Node):

    def __init__(self, llm: BaseChatModel):
        super().__init__(llm)
        self.state_description = SystemMessage(content=
        """
            You are currently in the collect phase of the kernel boot repair process. Your goal in this phase is to gather information
            from the original, bootable, configuration and the latest, non-bootable, configuration to either confirm or refute the current
            hypothesis. When you have sufficient evidence to support your hypothesis, run the kloclaizer tool and specify which options
            to define and undefine. If you do not have sufficient evidence, you may discard your current hypothesis and return to the analyze phase.                                          
        """)

    def collect(self, state) -> dict:
        pass

    def route(self, state) -> str:
        
        if state.current_hypothesis is None:
            return 'analyze'
        
        if state.messages[-1].tool_calls and state.messages[-1].tool_calls[0]['name'] == 'run_klocalizer':
            return 'analyze'

    def __get_tools(self, base_config: str, latest_config: str) -> list[callable]:
        
        @tool
        def discard_hypothesis() -> None:
            """
            Discards the current hypothesis and returns to the analyze phase to form a new hypothesis.
            Args: None
            Returns: None
            """
            return None
        
        @tool
        def search_base_config(options: list[str]) -> list[str]:
            """
            Searches the base configuration for the specified options and returns their values.
            Args:
                options (list[str]): A list of options to search for.
            Returns:
                list[str]: A list of strings in the format "OPTION=VALUE" for each option.
            """
            
            results = []
            with open(base_config, 'r', errors='replace') as f:
                lines = f.readlines()
                for option in options:
                    for line in lines:
                        if line.startswith(option + '='):
                            results.append(line.strip())

            return results

        @tool
        def search_latest_config(options: list[str]) -> list[str]:
            """
            Searches the latest configuration for the specified options and returns their values.
            Args:
                options (list[str]): A list of options to search for.
            Returns:
                list[str]: A list of strings in the format "OPTION=VALUE" for each option.
            """

            if not os.path.exists(latest_config):
                return [latest_config + ' does not exist.']
            
            results = []
            with open(latest_config, 'r', errors='replace') as f:
                lines = f.readlines()
                for option in options:
                    for line in lines:
                        if line.startswith(option + '='):
                            results.append(line.strip())

            return results

        return [discard_hypothesis, search_base_config, search_latest_config]

collect = CollectNode()
