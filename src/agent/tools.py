from langchain_core.tools import StructuredTool, tool
from src.models import ToolCall, EmbeddingUsage
from singleton_decorator import singleton
from src.config import settings
from .search import LogSearch
from .session import Session
import os

@singleton
class AgentTools:

    def __grep(self, path: str, pattern: str) -> list[str]:

        if not os.path.exists(path):
                return [f'{path} does not exist.']

        results = []
        with open(path, 'r', errors='replace') as f:
            for i, line in enumerate(f, 1):
                if pattern.lower() in line.lower():
                    results.append(f'{i + 1}: {line.strip()}')
        
        return results[-50:]
    
    def __chunk(self, path: str, line: int) -> list[str]:
        
        if not os.path.exists(path):
                return [f'{path} does not exist.']

        results = []
        with open(path, 'r', errors='replace') as f:
            lines = f.readlines()
            start = max(0, line - 25)
            end = min(len(lines), line + 25)
            for i in range(start, end):
                results.append(f'{i + 1}: {lines[i].strip()}')
        
        return results
    
    def __search_config(self, path: str, options: list[str]) -> list[str]:
        
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

    def __get_rag_tools(self, session: Session) -> list[StructuredTool]:

        prev_attempt = session.attempts[-2]

        build_rag = LogSearch(prev_attempt.build_log, type='build') if prev_attempt.build_log else None
        boot_rag = LogSearch(prev_attempt.boot_log, type='boot') if prev_attempt.boot_log else None

        embedding_usage = EmbeddingUsage(
            build_log_tokens=build_rag.token_usage if build_rag else 0,
            boot_log_tokens=boot_rag.token_usage if boot_rag else 0,
        )

        session.attempts[-1].embedding_usage = embedding_usage

        tools = []

        if build_rag:

            @tool
            def search_build_log(query: str) -> str:
                """
                Search for specific information in the build log of the latest attempt.

                Args:
                    query (str): A string query to search for in the build log.
                Returns:
                    str: A string containing the relevant information from the build log that matches the query
                """
                results, tokens = build_rag.query(query)
                session.attempts[-1].tool_calls.append(ToolCall(
                    name='search_build_log',
                    args={ 'query': query },
                    response=results,
                    token_usage=EmbeddingUsage(build_log_tokens=tokens),
                ))

                return results

            tools.append(search_build_log)

        if boot_rag:

            @tool
            def search_boot_log(query: str) -> str:
                """
                Search for specific information in the boot log of the latest attempt.

                Args:
                    query (str): A string query to search for in the boot log.
                Returns:
                    str: A string containing the relevant information from the boot log that matches the query
                """
                results, tokens = boot_rag.query(query)
                session.attempts[-1].tool_calls.append(ToolCall(
                    name='search_boot_log',
                    args={ 'query': query },
                    response=results,
                    token_usage=EmbeddingUsage(boot_log_tokens=tokens),
                ))

                return results

            tools.append(search_boot_log)

        return tools

    def __get_file_tools(self, session: Session) -> list[StructuredTool]:

        prev_attempt = session.attempts[-2]

        @tool
        def grep_build_log(pattern: str) -> str:
            """
            Search for specific patterns in the build log of the latest attempt.

            Args:
                pattern (str): A string pattern to search for in the build log.
            Returns:
                str: A string containing the lines from the build log that match the pattern.
            """
            results = self.__grep(prev_attempt.build_log, pattern)
            session.attempts[-1].tool_calls.append(ToolCall(
                name='grep_build_log',
                args={ 'pattern': pattern },
                response=results,
            ))

            return '\n'.join(results)

        @tool
        def chunk_build_log(line: int) -> str:
            """
            Get a chunk of lines from the build log of the latest attempt, centered around a specific line number.

            Args:
                line (int): The line number to center the chunk around in the build log.
            Returns:
                str: A string containing the lines from the build log that are within the chunk
            """
            results = self.__chunk(prev_attempt.build_log, line)
            session.attempts[-1].tool_calls.append(ToolCall(
                name='chunk_build_log',
                args={ 'line': line },
                response=results,
            ))

            return '\n'.join(results)

        @tool
        def grep_boot_log(pattern: str) -> str:
            """
            Search for specific patterns in the boot log of the latest attempt.

            Args:
                pattern (str): A string pattern to search for in the boot log.
            Returns:
                str: A string containing the lines from the boot log that match the pattern.
            """
            results = self.__grep(prev_attempt.boot_log, pattern)
            session.attempts[-1].tool_calls.append(ToolCall(
                name='grep_boot_log',
                args={ 'pattern': pattern },
                response=results,
            ))

            return '\n'.join(results)

        @tool
        def chunk_boot_log(line: int) -> str:
            """
            Get a chunk of lines from the boot log of the latest attempt, centered around a specific line number.

            Args:
                line (int): The line number to center the chunk around in the boot log.
            Returns:
                str: A string containing the lines from the boot log that are within the chunk
            """
            results = self.__chunk(prev_attempt.boot_log, line)
            session.attempts[-1].tool_calls.append(ToolCall(
                name='chunk_boot_log',
                args={ 'line': line },
                response=results,
            ))

            return '\n'.join(results)

        tools = []

        if prev_attempt.build_log is not None:
            tools.append(grep_build_log)
            tools.append(chunk_build_log)

        if prev_attempt.boot_log is not None:
            tools.append(grep_boot_log)
            tools.append(chunk_boot_log)

        return tools

    def get(self, session: Session) -> list[StructuredTool]:

        @tool
        def search_original_config(options: list[str]) -> str:
            """
            Search for the presence of specific configuration options in the original config file.
            
            Args:
                options (list[str]): A list of configuration options to search for in the original config file.
            Returns:
                str: A string containing the values of the options searched for that were found in the original config file.
            """
            results = self.__search_config(session.base, options)
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
            results = self.__search_config(session.latest, options)
            session.attempts[-1].tool_calls.append(ToolCall(
                name='search_latest_config',
                args={ 'options': options },
                response=results,
            ))

            return results

        tools = [search_original_config]

        if session.latest is not None or len(session.attempts) == 1:
            tools.append(search_latest_config)

        if settings.runtime.USE_RAG:
            tools.extend(self.__get_rag_tools(session))
        else:
            tools.extend(self.__get_file_tools(session))

        return tools

agent_tools = AgentTools()
