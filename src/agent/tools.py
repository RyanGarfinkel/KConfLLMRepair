from langchain_core.tools import StructuredTool, tool
from .session import Session
from src.utils import log
from .rag import RAG
import os

def search_config(path: str, options: list[str]) -> str:

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

    return '\n'.join(results)

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
        log.info('Agent is searching the original config.')
        return search_config(session.base, options)

    
    @tool
    def search_latest_config(options: list[str]) -> str:
        """
        Search for the presence of specific configuration options in the latest modified config file.
        
        Args:
            options (list[str]): A list of configuration options to search for in the latest modified config file.
        Returns:
            str: A string containing the values of the options searched for that were found in the latest modified config file.
        """
        log.info('Agent is searching the latest modified config.')
        return search_config(session.latest, options)
    
    klocalizer_rag = RAG(path=session.attempts[-1].klocalizer_log, type='klocalizer')
    build_rag = RAG(path=session.attempts[-1].build_log, type='build')
    boot_rag = RAG(path=session.attempts[-1].boot_log, type='qemu')

    tools = [search_original_config]

    if session.latest is not None or len(session.attempts) == 1:
        tools.append(search_latest_config)

    if session.attempts[-1].klocalizer_log is not None:
        tools.append(klocalizer_rag.as_tool(
            name='search_klocalizer_log',
            desc='Search for specific information in the KLocalizer log of the latest attempt.')
        )

    if session.attempts[-1].build_log is not None:
        tools.append(build_rag.as_tool(
            name='search_build_log',
            desc='Search for specific information in the build log of the latest attempt.')
        )

    if session.attempts[-1].boot_log is not None:
        tools.append(boot_rag.as_tool(
            name='search_boot_log',
            desc='Search for specific information in the boot log of the latest attempt.')
        )

    return tools
