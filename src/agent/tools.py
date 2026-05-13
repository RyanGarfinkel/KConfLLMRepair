from langchain_core.tools import StructuredTool, tool
from src.models import ToolCall, EmbeddingUsage
from singleton_decorator import singleton
from src.config import settings
from .search import LogSearch
from .session import Session
import re
import os

@singleton
class AgentTools:

    def __grep(self, path: str, pattern: str) -> list[str]:

        if not os.path.exists(path):
            return [f'{path} does not exist.']

        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error:
            compiled = re.compile(re.escape(pattern), re.IGNORECASE)

        results = []
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f, 1):
                if compiled.search(line):
                    results.append(f'{i}: {line.strip()}')

        if not results:
            return [f'No matches found for "{pattern}". Try a broader or different pattern.']

        total = len(results)
        truncated = results[:50]
        if total > 50:
            truncated.append(f'... {total - 50} more matches not shown. Narrow your pattern to see more relevant results.')

        return truncated
    
    def __chunk(self, path: str, line: int) -> list[str]:
        
        if not os.path.exists(path):
                return [f'{path} does not exist.']

        results = []
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
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
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
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

        if session.patch is not None:

            @tool
            def search_patch(options: list[str]) -> str:
                """
                Search for specific configuration options by name in the patch file.

                Args:
                    options (list[str]): A list of configuration option names to look up in the patch.
                Returns:
                    str: A string containing the lines from the patch that reference each option.
                """
                results = []
                for option in options:
                    matches = self.__grep(session.patch, option)
                    results.extend(matches if matches else [f'{option} not found in patch.'])

                session.attempts[-1].tool_calls.append(ToolCall(
                    name='search_patch',
                    args={ 'options': options },
                    response=results,
                ))

                return '\n'.join(results)

            tools.append(search_patch)

        return tools

    def __get_file_tools(self, session: Session) -> list[StructuredTool]:

        prev_attempt = session.attempts[-2]

        @tool
        def grep_patch(pattern: str) -> str:
            """
            Search for a pattern in the patch file that was applied to produce the broken config.

            Args:
                pattern (str): A string pattern to search for in the patch file.
            Returns:
                str: A string containing the lines from the patch file that match the pattern.
            """
            results = self.__grep(session.patch, pattern)
            session.attempts[-1].tool_calls.append(ToolCall(
                name='grep_patch',
                args={ 'pattern': pattern },
                response=results,
            ))

            return '\n'.join(results)

        @tool
        def chunk_patch(line: int) -> str:
            """
            Get a chunk of lines from the patch file centered around a specific line number.

            Args:
                line (int): The line number to center the chunk around.
            Returns:
                str: A string containing the lines from the patch file within the chunk.
            """
            results = self.__chunk(session.patch, line)
            session.attempts[-1].tool_calls.append(ToolCall(
                name='chunk_patch',
                args={ 'line': line },
                response=results,
            ))

            return '\n'.join(results)

        @tool
        def grep_build_log(pattern: str) -> str:
            """
            Search the build log of the latest attempt for lines matching a pattern.
            Start broad — patterns like "error:" are a good starting point — then narrow
            based on what you find. If nothing matches, try a simpler or shorter pattern.

            Args:
                pattern (str): Regex pattern to search for. Keep it broad - specific strings often match nothing.
            Returns:
                str: Matching lines with line numbers, or a message indicating no matches.
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
            Search the boot log of the latest attempt for lines matching a pattern.
            Start broad — patterns like "error|panic|failed" or "BUG|WARNING" are good
            starting points — then narrow based on what you find. If nothing matches,
            try a simpler or shorter pattern.

            Args:
                pattern (str): Regex pattern to search for. Keep it broad - specific strings often match nothing.
            Returns:
                str: Matching lines with line numbers, or a message indicating no matches.
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

        if session.patch is not None:
            tools.extend([grep_patch, chunk_patch])

        if prev_attempt.build_log is not None:
            tools.extend([grep_build_log, chunk_build_log])

        if prev_attempt.boot_log is not None:
            tools.extend([grep_boot_log, chunk_boot_log])

        return tools

    def get(self, session: Session) -> list[StructuredTool]:

        prev_config = session.attempts[-2].config if len(session.attempts) >= 2 else None

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
            results = self.__search_config(prev_config, options)
            session.attempts[-1].tool_calls.append(ToolCall(
                name='search_latest_config',
                args={ 'options': options },
                response=results,
            ))

            return results

        tools = [search_original_config]

        if prev_config is not None and prev_config != session.base:
            tools.append(search_latest_config)

        if settings.runtime.USE_RAG:
            tools.extend(self.__get_rag_tools(session))
        else:
            tools.extend(self.__get_file_tools(session))

        return tools

agent_tools = AgentTools()
