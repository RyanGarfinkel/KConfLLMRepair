from src.tools.klocalizer import KLocalizer
from src.kernel.builder import Builder
from src.kernel.kconfig import KConfig
from src.kernel.boot import does_boot
from src.utils.log import log_info
from langchain.tools import tool
from dotenv import load_dotenv
import subprocess
import os
import re

load_dotenv()

if not os.getenv('BASE_CONFIG'):
    raise EnvironmentError('BASE_CONFIG not set.')

_BASE_CONFIG = KConfig(os.getenv('BASE_CONFIG'))

def get_agent_tools(repo, dir):

    log_info('Initializing agent tools...')

    tries = 1

    klocalizer = KLocalizer()
    builder = Builder()

    if not os.path.exists(f'{dir}/try_0'):
        raise FileNotFoundError(f'Inital sample not found at {dir}/try_0.')

    config = KConfig(f'{dir}/try_0/klocalizer.config')

    @tool
    def search_klocalizer_log(regex: str) -> list[str]:
        """
        Searches the klocalizer logs for lines matching the given regular expression.

        Args:
            regex (str): Regular expression to search for in the klocalizer logs.
        Returns:
            list[str]: List of lines from the klocalizer logs that match the given regular expression.
        """
    
        try_dir = f'{dir}/try_{tries - 1}'
        log_path = f'{try_dir}/klocalizer.log'

        if not os.path.exists(log_path):
            return f'KLocalizer log not found at {log_path}. No logs to search.'
        
        with open(log_path, 'r') as f:
            lines = f.readlines()

        matching_lines = [line.strip() for line in lines if re.search(regex, line)]
        return matching_lines

    @tool
    def search_build_log(regex: str) -> list[str]:
        """
        Searches the build logs for lines matching the given regular expression.

        Args:
            regex (str): Regular expression to search for in the build logs.
        Returns:
            list[str]: List of lines from the build logs that match the given regular expression.
        """

        try_dir = f'{dir}/try_{tries - 1}'
        log_path = f'{try_dir}/build.log'

        if not os.path.exists(log_path):
            return f'Build log not found at {log_path}. No logs to search.'
        
        with open(log_path, 'r') as f:
            lines = f.readlines()

        matching_lines = [line.strip() for line in lines if re.search(regex, line)]
        return matching_lines

    @tool
    def search_qemu_log(regex: str) -> list[str]:
        """
        Searches the QEMU logs for lines matching the given regular expression.

        Args:
            regex (str): Regular expression to search for in the QEMU logs.
        Returns:
            list[str]: List of lines from the QEMU logs that match the given regular expression.
        """

        try_dir = f'{dir}/try_{tries - 1}'
        log_path = f'{try_dir}/qemu.log'

        if not os.path.exists(log_path):
            return f'QEMU log not found at {log_path}. No logs to search.'
        
        with open(log_path, 'r') as f:
            lines = f.readlines()

        matching_lines = [line.strip() for line in lines if re.search(regex, line)]
        return matching_lines

    @tool
    def get_base_config_value(option: str) -> str:
        """
        Gets the value of a configuration option from the base configuration.

        Args:
            option (str): The name of the configuration option to retrieve.
        Returns:
            str: The value of the configuration option, or a message indicating that the option is not set.
        """

        value = _BASE_CONFIG.get(option)
        if value is None or value is False:
            return f'# {option} is not set.'

        return f'{option}={value}'

    @tool
    def get_updated_config_value(option: str) -> str:
        """
        Gets the value of a configuration option from the updated configuration.

        Args:
            option (str): The name of the configuration option to retrieve.
        Returns:
            str: The value of the configuration option, or a message indicating that the option is not set.
        """
        
        value = config.get(option)
        if value is None or value is False:
            return f'# {option} is not set.'

        return f'{option}={value}'

    @tool
    def apply_and_test_changes(define: list[str], undefine: list[str]) -> str:
        """
        Applies the changes to the kernel configuration using klocalizer and tests the resulting kernel in QEMU.
        The boot log, delta from baseline, and new configuration will be updated after this tool runs.

        Args:
            define list[str]: List of configuration options that the klocalizer tool keeps enabled.
            undefine list[str]: List of configuration option names that the klocalizer tool keeps disabled.
        Returns:
            str: String indicating the result of applying and testing the changes.
        """

        nonlocal tries, config

        log_info(f'Applying and testing changes to configuration. Attempt {tries + 1}...')

        try_dir = f'{dir}/try_{tries}'
        os.makedirs(try_dir, exist_ok=True)
        tries += 1

        # KLocalizer repair
        updated_config = klocalizer.repair(repo.path, try_dir, define=define, undefine=undefine)
        if updated_config is None:
            return 'KLocalizer repair failed. No changes applied. You may view the klocalizer log.'

        config = updated_config

        # Building the image
        if not builder.make_olddefconfig(repo):
            return 'Failed to run make olddefconfig after klocalizer repair. No changes applied.'

        bzImg = builder.build_kernel(repo, try_dir)
        if not bzImg:
            return 'Failed to build the kernel after klocalizer repair. No changes applied. You may view the build log.'

        # QEMU test
        didBoot = does_boot(bzImg, try_dir)
        
        if didBoot:
            return 'Changes applied and tested successfully. You may stop now.'
        
        return 'QEMU test failed. No changes applied. You may view the qemu log.'
    
    log_info('Agent tools initialized successfully.')

    return [
        search_klocalizer_log,
        search_build_log,
        search_qemu_log,
        get_base_config_value,
        get_updated_config_value,
        apply_and_test_changes,
    ]
        