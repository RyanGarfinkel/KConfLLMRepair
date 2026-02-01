from .utils import make_command, grep_command, chunk_command
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from langchain.tools import tool
from src.models import State
from typing import Annotated

@tool
def express_hypothesis(hypothesis: str, state: Annotated[State, InjectedState], tool_id: Annotated[str, InjectedState('tool_call_id')]) -> Command:
    """
    Register a new hypothesis about why the build failed.
    Args:
        hypothesis: Reason for build failure.
    Returns: None
    """
    return make_command({
        'messages': [ToolMessage(
            tool_call_id=tool_id,
            name='express_hypothesis',
            content=hypothesis
        )],
        'hypothesis': state.get('hypothesis').model_copy(update={
            'current': hypothesis,
        }),
    }, goto='collect')

@tool
def grep_klocalizer_log(pattern: str, state: Annotated[State, InjectedState], tool_id: Annotated[str, InjectedState('tool_call_id')]) -> Command:
    """
    Search the klocalizer log for lines matching the given pattern.
    Args:
        pattern (str): The pattern to search for.
    Returns:
        list[str]: A list of lines with line numbers that match the pattern.
    """
    return grep_command(state.get('attempts')[-1], 'klocalizer', tool_id, pattern)

@tool
def chunk_klocalizer_log(line_start: int, state: Annotated[State, InjectedState], tool_id: Annotated[str, InjectedState('tool_call_id')]) -> Command:
    """
    Retrieve a chunk of lines from the klocalizer log.
    Args:
        line_start (int): The starting line number (0-indexed).
    Returns:
        str: The chunk of lines.
    """
    return chunk_command(state.get('attempts')[-1], 'klocalizer', tool_id, line_start)

@tool
def grep_build_log(pattern: str, state: Annotated[State, InjectedState], tool_id: Annotated[str, InjectedState('tool_call_id')]) -> Command:
    """
    Search the build log for lines matching the given pattern.
    Args:
        pattern (str): The pattern to search for.
    Returns:
        list[str]: A list of lines with line numbers that match the pattern.
    """
    return grep_command(state.get('attempts')[-1], 'build', tool_id, pattern)

@tool
def chunk_build_log(line_start: int, state: Annotated[State, InjectedState], tool_id: Annotated[str, InjectedState('tool_call_id')]) -> Command:
    """
    Retrieve a chunk of lines from the build log.
    Args:
        line_start (int): The starting line number (0-indexed).
    Returns:
        str: The chunk of lines.
    """
    return chunk_command(state.get('attempts')[-1], 'build', tool_id, line_start)

@tool
def grep_qemu_log(pattern: str, state: Annotated[State, InjectedState], tool_id: Annotated[str, InjectedState('tool_call_id')]) -> Command:
    """
    Search the QEMU boot log for lines matching the given pattern.
    Args:
        pattern (str): The pattern to search for.
    Returns:
        list[str]: A list of lines with line numbers that match the pattern.
    """
    return grep_command(state.get('attempts')[-1], 'qemu', tool_id, pattern)

@tool
def chunk_qemu_log(line_start: int, state: Annotated[State, InjectedState], tool_id: Annotated[str, InjectedState('tool_call_id')]) -> Command:
    """
    Retrieve a chunk of lines from the QEMU boot log.
    Args:
        line_start (int): The starting line number (0-indexed).
    Returns:
        str: The chunk of lines.
    """
    return chunk_command(state.get('attempts')[-1], 'qemu', tool_id, line_start)

analyze_tools = [
    express_hypothesis,
    grep_klocalizer_log,
    chunk_klocalizer_log,
    grep_build_log,
    chunk_build_log,
    grep_qemu_log,
    chunk_qemu_log,
]
