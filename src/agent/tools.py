from langchain_core.tools import StructuredTool, tool
from src.models import ToolCall, EmbeddingUsage
from .search import LogSearch
from .session import Session
import os

def grep(path: str, pattern: str) -> list[str]:
    
    if not os.path.exists(path):
        return [f'{path} does not exist.']

    results = []

    with open(path, 'r', errors='replace') as f:
        for i, line in enumerate(f):
            if pattern in line:
                results.append(f'{i + 1}:{line.strip()}')
    
    return results

def chunk(path: str, line: int) -> list[str]:

    if not os.path.exists(path):
        return [f'{path} does not exist.']

    results = []
    start = max(0, line - 15)
    end = line + 15

    with open(path, 'r', errors='replace') as f:
        for i, line in enumerate(f):
            if i >= start and i <= end:
                results.append(f'{i + 1}:{line.strip()}')
            elif i > end:
                break
    
    return results

def search_config(path: str, options: list[str]) -> list[str]:

    if not os.path.exists(path):
            return [f'{path} does not exist.']

    map = {}
    with open(path, 'r', errors='replace') as f:
        for line in f:
            line = line.strip()

            if '=' in line and not line.startswith('#'):
                key = line.split('=', 1)[0]
                map[key] = line
            elif line.startswith('# ') and line.endswith(' is not set'):
                key = line[2:-len(' is not set')]
                map[key] = line
    
    results = []
    for option in options:
        if option in map:
            results.append(map[option])
        else:
            results.append(f'{option} not found in config.')

    return results

def get_agent_tools(session: Session) -> list[StructuredTool]:

    @tool
    def search_original_config(options: list[str]) -> str:
        """
        Search for the presence of specific configuration options in the original config file.
        
        Args:
            options (list[str]): A list of configuration options to search for in the original config file.
        Returns:
            str: A string containing the values of the options searched for that were found in the original config file.
        """
        results = search_config(session.base, options)
        session.attempts[-1].tool_calls.append(ToolCall(
            name='search_original_config',
            args={ 'options': options },
            response=results,
        ))

        return results
    
    @tool
    def search_latest_config(options: list[str]) -> str:
        """
        Search for the presence of specific configuration options in the latest modified config file.
        
        Args:
            options (list[str]): A list of configuration options to search for in the latest modified config file.
        Returns:
            str: A string containing the values of the options searched for that were found in the latest modified config file.
        """
        results = search_config(session.latest, options)
        session.attempts[-1].tool_calls.append(ToolCall(
            name='search_latest_config',
            args={ 'options': options },
            response=results,
        ))

        return results
    
    klocalizer_rag = LogSearch(session.attempts[-2].klocalizer_log, type='klocalizer')
    build_rag = LogSearch(session.attempts[-2].build_log, type='build')
    boot_rag = LogSearch(path=session.attempts[-2].boot_log, type='boot')

    session.attempts[-1].embedding_usage = EmbeddingUsage(
        klocalizer_log_tokens=klocalizer_rag.token_usage,
        build_log_tokens=build_rag.token_usage,
        boot_log_tokens=boot_rag.token_usage,
    )

    @tool
    def search_klocalizer_log(query: str) -> str:
        """
        Search for specific information in the KLocalizer log of the latest attempt.

        Args:
            query (str): A string query to search for in the KLocalizer log.
        Returns:
            str: A string containing the relevant information from the KLocalizer log that matches the query
        """
        results, token_usage = klocalizer_rag.query(query)
        session.attempts[-1].tool_calls.append(ToolCall(
            name='search_klocalizer_log',
            args={ 'query': query },
            response=results,
            token_usage=token_usage,
        ))

        return results
    
    @tool
    def search_build_log(query: str) -> str:
        """
        Search for specific information in the build log of the latest attempt.

        Args:
            query (str): A string query to search for in the build log.
        Returns:
            str: A string containing the relevant information from the build log that matches the query
        """
        results, token_usage = build_rag.query(query)
        session.attempts[-1].tool_calls.append(ToolCall(
            name='search_build_log',
            args={ 'query': query },
            response=results,
            token_usage=token_usage,
        ))

        return results
    
    @tool
    def search_boot_log(query: str) -> str:
        """
        Search for specific information in the boot log of the latest attempt.

        Args:
            query (str): A string query to search for in the boot log.
        Returns:
            str: A string containing the relevant information from the boot log that matches the query
        """
        results, token_usage = boot_rag.query(query)
        session.attempts[-1].tool_calls.append(ToolCall(
            name='search_boot_log',
            args={ 'query': query },
            response=results,
            token_usage=token_usage,
        ))

        return results
    
    tools = [search_original_config]

    if session.latest is not None or len(session.attempts) == 1:
        tools.append(search_latest_config)

    if session.attempts[-2].klocalizer_log is not None:
        tools.append(search_klocalizer_log)

    if session.attempts[-2].build_log is not None:
        tools.append(search_build_log)

    if session.attempts[-2].boot_log is not None:
        tools.append(search_boot_log)
        
    return tools
