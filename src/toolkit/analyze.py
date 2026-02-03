from langchain.tools import tool
from src.tools import file

def analyze_tools(patch: str, klocalizer_log: str | None, build_log: str | None, boot_log: str | None):

    @tool
    def express_hypothesis(hypothesis: str) -> str:
        """
        Register a new hypothesis about why the build failed.
        Args: hypothesis: Reason for build failure.
        Returns: None
        """
        return hypothesis

    @tool
    def grep_patch(pattern: str) -> str:
        """
        Search the patch file for lines matching the given pattern.
        Args: pattern (str): The pattern to search for.
        Returns: str: A string containing lines with line numbers that match the pattern.
        """
        return '\n'.join(file.grep(patch, pattern))

    @tool
    def chunk_patch(line_start: int) -> str:
        """
        Retrieve a chunk of lines from the patch file.
        Args: line_start (int): The starting line number (0-indexed).
        Returns: str: The chunk of lines.
        """
        return '\n'.join(file.chunk(patch, line_start))

    @tool
    def grep_klocalizer_log(pattern: str) -> str:
        """
        Search the klocalizer log for lines matching the given pattern.
        Args: pattern (str): The pattern to search for.
        Returns: str: A string containing lines with line numbers that match the pattern.
        """
        return '\n'.join(file.grep(klocalizer_log, pattern))

    @tool
    def chunk_klocalizer_log(line_start: int) -> str:
        """
        Retrieve a chunk of lines from the klocalizer log.
        Args: line_start (int): The starting line number (0-indexed).
        Returns: str: The chunk of lines.
        """
        return '\n'.join(file.chunk(klocalizer_log, line_start))
    
    @tool
    def grep_build_log(pattern: str) -> str:
        """
        Search the build log for lines matching the given pattern.
        Args: pattern (str): The pattern to search for.
        Returns: str: A string containing lines with line numbers that match the pattern.
        """
        return '\n'.join(file.grep(build_log, pattern))

    @tool
    def chunk_build_log(line_start: int) -> str:
        """
        Retrieve a chunk of lines from the build log.
        Args: line_start (int): The starting line number (0-indexed).
        Returns: str: The chunk of lines.
        """
        return '\n'.join(file.chunk(build_log, line_start))

    @tool
    def grep_boot_log(pattern: str) -> str:
        """
        Search the QEMU boot log for lines matching the given pattern.
        Args: pattern (str): The pattern to search for.
        Returns: str: A string containing lines with line numbers that match the pattern.
        """
        return '\n'.join(file.grep(boot_log, pattern))

    @tool
    def chunk_boot_log(line_start: int) -> str:
        """
        Retrieve a chunk of lines from the QEMU boot log.
        Args: line_start (int): The starting line number (0-indexed).
        Returns: str: The chunk of lines.
        """
        return '\n'.join(file.chunk(boot_log, line_start))

    return [
        express_hypothesis,
        grep_patch,
        chunk_patch,
        grep_klocalizer_log,
        chunk_klocalizer_log,
        grep_build_log,
        chunk_build_log,
        grep_boot_log,
        chunk_boot_log,
    ]
