from langchain_core.tools import StructuredTool, tool
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

def get_agent_tools(base: str | None, patch: str | None, modified: str, build: str, boot: str) -> list[StructuredTool]:

    @tool
    def search_base_config(options: list[str]) -> str:
        """
        Search for the presence of specific configuration options in the base config file.
        
        Args:
            options (list[str]): A list of configuration options to search for in the base config file.
        Returns:
            str: A string containing the values of the options searched for that were found in the base config file.
        """
        return search_config(base, options)
    
    @tool
    def search_latest_config(options: list[str]) -> str:
        """
        Search for the presence of specific configuration options in the latest modified config file.
        
        Args:
            options (list[str]): A list of configuration options to search for in the latest modified config file.
        Returns:
            str: A string containing the values of the options searched for that were found in the latest modified config file.
        """
        return search_config(modified, options)
    
    build_rag = RAG(path=build, type='build')
    boot_rag = RAG(path=boot, type='qemu')

    tools = [
        search_latest_config,
        build_rag.as_tool(
            name='search_build_log',
            desc='Search the build log for relevant information about build errors and warnings encountered during this attempt.'
        ),
        boot_rag.as_tool(
            name='search_qemu_log',
            desc='Search the QEMU log for relevant information about runtime errors and kernel panics encountered during this attempt.'
        )
    ]

    if base:
        tools.insert(0, search_base_config)

    if patch:
        patch_rag = RAG(path=patch, type='patch')
        tools.append(
            patch_rag.as_tool(
                name='search_patch',
                desc='Search the patch file for relevant information about code changes made in this attempt.'
            )
        )

    return tools
