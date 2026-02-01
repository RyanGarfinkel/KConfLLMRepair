
from .utils import make_command, search_config_command
from langchain.core.runnable import RunnableConfig
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from langchain.tools import tool
from src.models import State
from typing import Annotated

@tool
def discard_hypothesis(state: Annotated[State, InjectedState], tool_id: Annotated[str, InjectedState('tool_call_id')]) -> Command:
    """
    Discards the current hypothesis and returns to the analyze phase to form a new hypothesis.
    Args: None
    Returns: None
    """
    old_hypothesis = state.get('hypothesis')
    hypothesis = state.get('hypothesis').model_copy(update={
        'current': None,
        'history': old_hypothesis.history + [{
            'guess': old_hypothesis.current,
            'status': 'discarded'
        }]
    })

    return make_command({
        'messages': [
            ToolMessage(
                tool_call_id=tool_id,
                name='discard_hypothesis',
                content='Hypothesis discarded.'
            )
        ],
        'hypothesis': hypothesis,
    }, goto='analyze')
    
@tool
def search_base_config(options: list[str], state: Annotated[State, InjectedState], tool_id: Annotated[str, InjectedState('tool_call_id')]) -> Command:
    """
    Searches the base configuration for the specified options and returns their values.
    Args:
        options (list[str]): A list of options to search for.
    Returns:
        list[str]: A list of strings in the format "OPTION=VALUE" for each option.
    """
    return search_config_command(path=state.get('base_config'), options=options, id=tool_id, tool_name='search_base_config')

@tool
def search_latest_config(options: list[str], state: Annotated[State, InjectedState], tool_id: Annotated[str, InjectedState('tool_call_id')]) -> Command:
    """
    Searches the latest configuration for the specified options and returns their values.
    Args:
        options (list[str]): A list of options to search for.
    Returns:
        list[str]: A list of strings in the format "OPTION=VALUE" for each option.
    """
    return search_config_command(path=state.get('attempts')[-1].config, options=options, id=tool_id, tool_name='search_latest_config')

def run_klocalizer(define: list[str], undefine: list[str], state: Annotated[State, InjectedState], config: RunnableConfig, tool_id: Annotated[str, InjectedState('tool_call_id')]) -> str:
    """
    Runs the klocalizer tool with the specified configuration changes. If there is a satisfying configuration,
    it will include the options in 'define' and exclude the options in 'undefine'.

    Args:
        define list[str]: List of configuration options that the klocalizer tool keeps enabled.
        undefine list[str]: List of configuration option names that the klocalizer tool keeps disabled.
    Returns:
        list[str]: A list of messages indicating the result of applying and testing the changes.
    """
    pass

collect_tools = [
    discard_hypothesis,
    search_base_config,
    search_latest_config,
    run_klocalizer,
]
