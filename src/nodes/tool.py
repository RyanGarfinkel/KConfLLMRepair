
from langgraph.prebuilt import InjectedState, ToolNode
from langgraph.types import Command
from langchain.tools import tool
from typing import Annotated
from src.models import State
import os
    
# Analyze Functions

def __grep(log_path: str | None, pattern: str) -> list[str]:

        if not log_path:
            return ['Log file does not exist.']

        if not os.path.exists(log_path):
            return [os.path.basename(log_path) + ' does not exist.']

        results = []

        with open(log_path, 'r', errors='replace') as f:
            for i, line in enumerate(f):
                if pattern in line:
                    results.append(f'Line {i + 1}: {line.strip()}')

        return results

def __chunk(log_path: str | None, line_start: int, num_lines: int) -> str:

    if not log_path:
        return 'Log file does not exist.'
    
    if not os.path.exists(log_path):
        return log_path + ' does not exist.'

    chunk_lines = []

    with open(log_path, 'r', errors='replace') as f:
        for i, line in enumerate(f):
            if i >= line_start and i < line_start + num_lines:
                chunk_lines.append(f'Line {i + 1}: {line.strip()}')
            if i >= line_start + num_lines:
                break

    return '\n'.join(chunk_lines)

@tool
def express_hypothesis(hypothesis: str, state: Annotated[State, InjectedState]) -> Command:
    """
    Register a new hypothesis about why the build failed.
    
    Args:
        hypothesis: The technical theory (e.g. "Missing CONFIG_VIRTIO_BLK symbol").
    Returns: None
    """
    hypothesis = state.get('hypothesis').model_copy(update={
        'current': hypothesis,
    })

    return Command(update={
        'hypothesis': hypothesis,
    })

@tool
def grep_klocalizer_log(pattern: str, state: Annotated[State, InjectedState]) -> list[str]:
    """
    Search the klocalizer log for lines matching the given pattern.
    Args:
        pattern (str): The pattern to search for.
    Returns:
        list[str]: A list of lines with line numbers that match the pattern.
    """
    if not state.attempts:
        return ['The latest klocalizer log does not exist.']

    log_path = state.attempts[-1].klocalizer_log
    return __grep(log_path, pattern)

@tool
def chunk_klocalizer_log(line_start: int, num_lines: int, state: Annotated[State, InjectedState]) -> str:
    """
    Retrieve a chunk of lines from the klocalizer log.
    Args:
        line_start (int): The starting line number (0-indexed).
        num_lines (int): The number of lines to retrieve.
    Returns:
        str: The chunk of lines.
    """
    if not state.attempts:
        return 'The latest klocalizer log does not exist.'

    log_path = state.attempts[-1].klocalizer_log
    return __chunk(log_path, line_start, num_lines)

@tool
def grep_build_log(pattern: str, state: Annotated[State, InjectedState]) -> list[str]:
    """
    Search the build log for lines matching the given pattern.
    Args:
        pattern (str): The pattern to search for.
    Returns:
        list[str]: A list of lines with line numbers that match the pattern.
    """
    if not state.attempts:
        return ['Build log does not exist.']
    
    log_path = state.attempts[-1].build_log
    return __grep(log_path, pattern)

@tool
def chunk_build_log(line_start: int, num_lines: int, state: Annotated[State, InjectedState]) -> str:
    """
    Retrieve a chunk of lines from the build log.
    Args:
        line_start (int): The starting line number (0-indexed).
        num_lines (int): The number of lines to retrieve.
    Returns:
        str: The chunk of lines.
    """
    if not state.attempts:
        return 'Build log does not exist.'

    log_path = state.attempts[-1].build_log
    return __chunk(log_path, line_start, num_lines)

@tool
def grep_qemu_log(pattern: str, state: Annotated[State, InjectedState]) -> list[str]:
    """
    Search the QEMU boot log for lines matching the given pattern.
    Args:
        pattern (str): The pattern to search for.
    Returns:
        list[str]: A list of lines with line numbers that match the pattern.
    """
    if not state.attempts:
        return ['Boot log does not exist.']
    
    log_path = state.attempts[-1].boot_log
    return __grep(log_path, pattern)

@tool
def chunk_qemu_log(line_start: int, num_lines: int, state: Annotated[State, InjectedState]) -> str:
    """
    Retrieve a chunk of lines from the QEMU boot log.
    Args:
        line_start (int): The starting line number (0-indexed).
        num_lines (int): The number of lines to retrieve.
    Returns:
        str: The chunk of lines.
    """
    if not state.attempts:
        return 'Boot log does not exist.'

    log_path = state.attempts[-1].boot_log
    return __chunk(log_path, line_start, num_lines)

# Collect Functions

@tool
def discard_hypothesis(state: Annotated[State, InjectedState]) -> Command:
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

    return Command(update={
        'hypothesis': hypothesis,
    }, goto='analyze')
    
@tool
def search_base_config(options: list[str], state: Annotated[State, InjectedState]) -> list[str]:
    """
    Searches the base configuration for the specified options and returns their values.
    Args:
        options (list[str]): A list of options to search for.
    Returns:
        list[str]: A list of strings in the format "OPTION=VALUE" for each option.
    """
    
    results = []
    with open(state.base_config, 'r', errors='replace') as f:
        lines = f.readlines()
        for option in options:
            for line in lines:
                if line.startswith(option + '='):
                    results.append(line.strip())

    return results

@tool
def search_latest_config(options: list[str], state: Annotated[State, InjectedState]) -> list[str]:
    """
    Searches the latest configuration for the specified options and returns their values.
    Args:
        options (list[str]): A list of options to search for.
    Returns:
        list[str]: A list of strings in the format "OPTION=VALUE" for each option.
    """
    if not state.attempts or not state.attempts[-1].config:
        return ['The latest configuration file does not exist.']
    
    latest_config = state.attempts[-1].config
    
    results = []
    with open(latest_config, 'r', errors='replace') as f:
        lines = f.readlines()
        for option in options:
            for line in lines:
                if line.startswith(option + '='):
                    results.append(line.strip())

    return results

def run_klocalizer(define: list[str], undefine: list[str], state: Annotated[State, InjectedState]) -> str:
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

# Main

analyze_tools = [
    express_hypothesis,
    grep_klocalizer_log,
    chunk_klocalizer_log,
    grep_build_log,
    chunk_build_log,
    grep_qemu_log,
    chunk_qemu_log,
]

collect_tools = [
    discard_hypothesis,
    search_base_config,
    search_latest_config,
]

tool = ToolNode(analyze_tools + collect_tools)
