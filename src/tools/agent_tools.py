from langchain_core.tools import StructuredTool
from src.config import settings
from src.kernel import KConfig
from src.models import Sample
from src.tools import booter
from src.utils import log
import shutil
import os
import re

class AgentTools:

    def __init__(self, kernel: 'Kernel', sample: Sample):

        self.kernel = kernel
        self.output_dir = f'{settings.EXPERIMENT_DIR}/sample_{sample.id}'
        self.try_count = 1

        if not os.path.exists(f'{settings.SAMPLE_DIR}/sample_{sample.id}'):
            raise Exception(f'Sample directory {self.output_dir} does not exist. Cannot initialize AgentTools for sample {sample.id}.')

        os.makedirs(self.output_dir, exist_ok=True)
        shutil.copytree(sample.dir, f'{self.output_dir}/try_0', dirs_exist_ok=True)

        self.patch_file = f'{self.output_dir}/try_0/changes.patch'
        if not os.path.exists(self.patch_file):
            raise Exception(f'Patch file {self.patch_file} does not exist. Cannot initialize AgentTools for sample {sample.id}.')

        self.base_config = KConfig(settings.BASE_CONFIG)
        self.succeeded = False

    @property
    def config(self) -> str:
        return f'{self.output_dir}/try_{self.try_count - 1}/klocalizer.config'
    
    def search_patch(self, regex: str) -> list[str]:
        """
        Search for lines in the patch that match the given regex pattern.
        
        Args:
            regex (str): The regular expression pattern to search for in the patch file.
        Returns:
            list[str]: A list of lines from the patch file that match the regex pattern.
        """

        log.info(f'Agent is searching for pattern "{regex}" in the patch file.')

        with open(self.patch_file, 'r') as f:
            lines = f.readlines()

        try:
            matches = [line.strip() for line in lines if re.search(regex, line)]
        except re.error as e:
            return [f'Error. Invalid regular expression: {e}']

        return self.__truncate(matches)

    def search_klocalizer_log(self, regex: str) -> list[str]:
        """
        Search for lines in the KLocalizer log that match the given regex pattern.
        
        Args:
            regex (str): The regular expression pattern to search for in the KLocalizer log file.
        Returns:
            list[str]: A list of lines from the KLocalizer log file that match the regex pattern.
        """

        log.info(f'Agent is searching for pattern "{regex}" in the klocalizer log file.')

        klocalizer_log = f'{self.output_dir}/try_{self.try_count - 1}/klocalizer.log'

        if not os.path.exists(klocalizer_log):
            return ['Error. There was no KLocalizer log for the latest try.']

        with open(klocalizer_log, 'r') as f:
            lines = f.readlines()

        try:
            matches = [line.strip() for line in lines if re.search(regex, line)]
        except re.error as e:
            return [f'Error. Invalid regular expression: {e}']

        return self.__truncate(matches)

    def search_build_log(self, regex: str) -> list[str]:
        """
        Search for lines in the build log that match the given regex pattern.
        
        Args:
            regex (str): The regular expression pattern to search for in the build log file.
        Returns:
            list[str]: A list of lines from the build log file that match the regex pattern.
        """

        log.info(f'Agent is searching for pattern "{regex}" in the build log file.')

        build_log = f'{self.output_dir}/try_{self.try_count - 1}/build.log'

        if not os.path.exists(build_log):
            return ['Error. There was no build log for the latest try.']

        with open(build_log, 'r') as f:
            lines = f.readlines()

        try:
            matches = [line.strip() for line in lines if re.search(regex, line)]
        except re.error as e:
            return [f'Error. Invalid regular expression: {e}']

        return self.__truncate(matches)
    
    def search_qemu_log(self, regex: str) -> list[str]:
        """
        Search for lines in the QEMU boot log that match the given regex pattern.
        
        Args:
            regex (str): The regular expression pattern to search for in the QEMU boot log file.
        Returns:
            list[str]: A list of lines from the QEMU boot log file that match the regex pattern.
        """

        log.info(f'Agent is searching for pattern "{regex}" in the QEMU boot log file.')

        qemu_log = f'{self.output_dir}/try_{self.try_count - 1}/qemu.log'

        if not os.path.exists(qemu_log):
            return ['Error. There was no QEMU boot log for the latest try.']

        with open(qemu_log, 'r') as f:
            lines = f.readlines()

        try:
            matches = [line.strip() for line in lines if re.search(regex, line)]
        except re.error as e:
            return [f'Error. Invalid regular expression: {e}']

        return self.__truncate(matches)

    def search_base_config(self, options: list[str]) -> list[str]:
        """
        Search for the presence of specific configuration options in the base config file.
        
        Args:
            options (list[str]): A list of configuration options to search for in the base config file.
        Returns:
            list[str]: A list of values of the options searched for that were found in the base config file.
        """

        log.info(f'Agent is searching for options {options} in the base config file.')

        values = []
        for option in options:
            value = self.base_config.options.get(option, None)
            if value is not None:
                values.append(f'{option}={value}')
            else:
                values.append(f'{option} not found in base config.')

        return values

    def search_latest_config(self, options: list[str]) -> list[str]:
        """
        Search for the presence of specific configuration options in the KLocalizer config file.
        
        Args:
            options (list[str]): A list of configuration options to search for in the KLocalizer config file.
        Returns:
            list[str]: A list of values of the options searched for that were found in the KLocalizer config file.
        """

        log.info(f'Agent is searching for options {options} in the latest KLocalizer config file.')

        klocalizer_config = f'{self.output_dir}/try_{self.try_count - 1}/klocalizer.config'

        if not os.path.exists(klocalizer_config):
            return ['Error. There was no KLocalizer config file for the latest try.']

        config = KConfig(klocalizer_config)

        values = []
        for option in options:
            value = config.options.get(option, None)
            if value is not None:
                values.append(f'{option}={value}')
            else:
                values.append(f'{option} not found in KLocalizer config.')

        return values

    def apply_and_test(self, define: list[str], undefine: list[str]) -> list[str]:
        """
        Applies the changes to the kernel configuration using klocalizer and tests the resulting kernel in QEMU.
        The boot log, delta from baseline, and new configuration will be updated after this tool runs.

        Args:
            define list[str]: List of configuration options that the klocalizer tool keeps enabled.
            undefine list[str]: List of configuration option names that the klocalizer tool keeps disabled.
        Returns:
            list[str]: A list of messages indicating the result of applying and testing the changes.
        """

        if self.succeeded:
            return ['The agent has already succeeded. No further changes are needed.']

        log.info('Agent is applying changes to the kernel configuration.')

        dir = f'{self.output_dir}/try_{self.try_count}'
        os.makedirs(dir, exist_ok=True)
        shutil.copy(self.patch_file, f'{dir}/changes.patch')
        self.try_count += 1

        self.base_config.cp(f'{self.kernel.repo.path}/.config')

        if not self.kernel.run_klocalizer(dir, define, undefine):
            return [f'Error. KLocalizer failed to run. Check the log for details.', self.__tail(f"{dir}/klocalizer.log")]

        if not self.kernel.build(dir):
            return [f'Error. Kernel build failed. Check the log for details.', self.__tail(f"{dir}/build.log")]
        
        if not booter.test(self.kernel, dir):
            return [f'Error. QEMU boot failed. Check the log for details.', self.__tail(f"{dir}/qemu.log")]

        self.succeeded = True   

        return [f'Success. Kernel built and booted successfully. You may finish now.']

    def __tail(self, file_path: str, n: int = 10) -> str:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            return ''.join(lines[-n:])
    
    def __truncate(self, matches: list[str], limit: int = 20) -> list[str]:
        if len(matches) > limit:
            amt = len(matches) - limit
            print(f'Found {len(matches)} matches, truncating to the last {limit} lines. ({amt} lines truncated)')
            return matches[-limit:] + [f'... (truncated {amt} lines)']
        
        print(f'Found {len(matches)} matches, no truncation needed.')
        return matches

    def get_tools(self) -> list[callable]:
        return [
            StructuredTool.from_function(
                func=self.search_patch,
                name='search_patch',
                description=self.search_patch.__doc__
            ),
            StructuredTool.from_function(
                func=self.search_klocalizer_log,
                name='search_klocalizer_log',
                description=self.search_klocalizer_log.__doc__
            ),
            StructuredTool.from_function(
                func=self.search_build_log,
                name='search_build_log',
                description=self.search_build_log.__doc__
            ),
            StructuredTool.from_function(
                func=self.search_qemu_log,
                name='search_qemu_log',
                description=self.search_qemu_log.__doc__
            ),
            StructuredTool.from_function(
                func=self.search_base_config,
                name='search_base_config',
                description=self.search_base_config.__doc__
            ),
            StructuredTool.from_function(
                func=self.search_latest_config,
                name='search_latest_config',
                description=self.search_latest_config.__doc__
            ),
            StructuredTool.from_function(
                func=self.apply_and_test,
                name='apply_and_test',
                description=self.apply_and_test.__doc__
            )
        ]
