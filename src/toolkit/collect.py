from langchain.tools import tool
from src.core import Kernel
from src.tools import file

def collect_tools(base_config: str, modified_config: str | None, patch: str, kernel: Kernel):

    @tool
    def discard_hypothesis() -> str:
        """
        Discards the current hypothesis and returns to the analyze phase to form a new hypothesis.
        Args: None
        Returns: str: A message indicating that the hypothesis has been discarded.
        """
        return 'Hypothesis discarded.'
        
    @tool
    def search_base_config(options: list[str]) -> str:
        """
        Searches the base configuration for the specified options and returns their values.
        Args: options (list[str]): A list of options to search for.
        Returns: list[str]: A list of strings with the status of each option
        """
        return '\n'.join(file.search_config(base_config, options))

    @tool
    def search_latest_config(options: list[str]) -> str:
        """
        Searches the latest configuration for the specified options and returns their values.
        Args: options (list[str]): A list of options to search for.
        Returns:list[str]: A list of strings in the format "OPTION=VALUE" for each option.
        """
        return '\n'.join(file.search_config(modified_config, options))

    @tool
    def run_klocalizer(define: list[str], undefine: list[str]) -> str:
        """
        Runs the klocalizer tool with the specified configuration changes. If there is a satisfying configuration,
        it will include the options in 'define' and exclude the options in 'undefine'.
        Args:
            define list[str]: List of configuration options that the klocalizer tool keeps enabled.
            undefine list[str]: List of configuration option names that the klocalizer tool keeps disabled.
        Returns:
            list[str]: A list of messages indicating the result of applying and testing the changes.
        """

        if not kernel.load_config(base_config):
            return 'ERROR: Could not load base configuration.'
        
        if not kernel.run_klocalizer(patch, f'{kernel.src}/klocalizer.log', define, undefine):
            return 'ERROR: KLocalizer failed to run.'

        return 'SUCCESS: KLocalizer completed and produced a new configuration. Attempting to build boot...'

    return [
        discard_hypothesis,
        search_base_config,
        search_latest_config,
        run_klocalizer
    ]
