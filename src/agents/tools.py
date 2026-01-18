from langchain_core.tools import StructuredTool
from src.kernel import KConfig
from src.models import Sample
from src.core import Kernel
import shutil
import os
import re

class Tools:

    def __init__(self, sample: Sample):

        self.output_dir = sample.output
        self.kernel = Kernel(sample.kernel_src)
        
        if not os.path.exists(f'{self.output_dir}/attempt_0'):
            raise Exception(f'Output directory {self.output_dir}/attempt_0 does not exist. Please run the initial attempt first.')

        self.tools_used = []
        self.succeeded = False
        self.attempt = 1
        self.base_config = KConfig(f'{self.output_dir}/attempt_0/base.config')

    @property
    def patch_file(self) -> str:
        return f'{self.output_dir}/attempt_0/changes.patch'

    @property
    def config(self) -> str:
        return f'{self.output_dir}/attempt_{self.attempt - 1}/modified.config'

    @property
    def latest_log(self) -> str:

        # QEMU log
        qemu_log = f'{self.output_dir}/attempt_{self.attempt - 1}/qemu.log'
        if os.path.exists(qemu_log):
            with open(qemu_log, 'r') as f:
                return ' '.join(self.__truncate(f.readlines()))
        
        # Build log
        build_log = f'{self.output_dir}/attempt_{self.attempt - 1}/build.log'
        if os.path.exists(build_log):
            with open(build_log, 'r') as f:
                return ' '.join(self.__truncate(f.readlines()))
            
        # KLocalizer log
        klocalizer_log = f'{self.output_dir}/attempt_{self.attempt - 1}/klocalizer.log'
        if os.path.exists(klocalizer_log):
            with open(klocalizer_log, 'r') as f:
                return ' '.join(self.__truncate(f.readlines()))
            
        return 'No logs available for the latest try.'
    
    # Agent Tools

    def search_patch(self, regex: str) -> list[str]:
        """
        Search for lines in the patch that match the given regex pattern.
        
        Args:
            regex (str): The regular expression pattern to search for in the patch file.
        Returns:
            list[str]: A list of lines from the patch file that match the regex pattern.
        """

        with open(self.patch_file, 'r') as f:
            lines = f.readlines()

        try:
            matches = [line.strip() for line in lines if re.search(regex, line)]
        except re.error as e:
            return [f'Error. Invalid regular expression: {e}']
        
        matches = self.__truncate(matches)

        self.tools_used.append({
            'tool': 'search_patch',
            'regex': regex,
            'matches': matches,
        })

        return matches

    def search_klocalizer_log(self, regex: str) -> list[str]:
        """
        Search for lines in the KLocalizer log that match the given regex pattern.
        
        Args:
            regex (str): The regular expression pattern to search for in the KLocalizer log file.
        Returns:
            list[str]: A list of lines from the KLocalizer log file that match the regex pattern.
        """

        klocalizer_log = f'{self.output_dir}/attempt_{self.attempt - 1}/klocalizer.log'

        if not os.path.exists(klocalizer_log):
            return ['Error. There was no KLocalizer log for the latest try.']

        with open(klocalizer_log, 'r') as f:
            lines = f.readlines()

        try:
            matches = [line.strip() for line in lines if re.search(regex, line)]
        except re.error as e:
            return [f'Error. Invalid regular expression: {e}']
        
        matches = self.__truncate(matches)

        self.tools_used.append({
            'tool': 'search_klocalizer_log',
            'regex': regex,
            'matches': matches,
        })

        return matches

    def search_build_log(self, regex: str) -> list[str]:
        """
        Search for lines in the build log that match the given regex pattern.
        
        Args:
            regex (str): The regular expression pattern to search for in the build log file.
        Returns:
            list[str]: A list of lines from the build log file that match the regex pattern.
        """

        build_log = f'{self.output_dir}/attempt_{self.attempt - 1}/build.log'

        if not os.path.exists(build_log):
            return ['Error. There was no build log for the latest try.']

        with open(build_log, 'r') as f:
            lines = f.readlines()

        try:
            matches = [line.strip() for line in lines if re.search(regex, line)]
        except re.error as e:
            return [f'Error. Invalid regular expression: {e}']

        matches = self.__truncate(matches)

        self.tools_used.append({
            'tool': 'search_build_log',
            'regex': regex,
            'matches': matches,
        })

        return matches
    
    def search_qemu_log(self, regex: str) -> list[str]:
        """
        Search for lines in the QEMU boot log that match the given regex pattern.
        
        Args:
            regex (str): The regular expression pattern to search for in the QEMU boot log file.
        Returns:
            list[str]: A list of lines from the QEMU boot log file that match the regex pattern.
        """

        qemu_log = f'{self.output_dir}/attempt_{self.attempt - 1}/qemu.log'

        if not os.path.exists(qemu_log):
            return ['Error. There was no QEMU boot log for the latest try.']

        with open(qemu_log, 'r') as f:
            lines = f.readlines()

        try:
            matches = [line.strip() for line in lines if re.search(regex, line)]
        except re.error as e:
            return [f'Error. Invalid regular expression: {e}']

        matches = self.__truncate(matches)

        self.tools_used.append({
            'tool': 'search_qemu_log',
            'regex': regex,
            'matches': matches,
        })

        return matches

    def search_base_config(self, options: list[str]) -> list[str]:
        """
        Search for the presence of specific configuration options in the base config file.
        
        Args:
            options (list[str]): A list of configuration options to search for in the base config file.
        Returns:
            list[str]: A list of values of the options searched for that were found in the base config file.
        """

        values = []
        for option in options:
            value = self.base_config.options.get(option, None)
            if value is not None:
                values.append(f'{option}={value}')
            else:
                values.append(f'{option} not found in base config.')

        self.tools_used.append({
            'tool': 'search_base_config',
            'options': options,
            'values': values,
        })

        return values

    def search_latest_config(self, options: list[str]) -> list[str]:
        """
        Search for the presence of specific configuration options in the KLocalizer config file.
        
        Args:
            options (list[str]): A list of configuration options to search for in the KLocalizer config file.
        Returns:
            list[str]: A list of values of the options searched for that were found in the KLocalizer config file.
        """

        klocalizer_config = f'{self.output_dir}/attempt_{self.attempt - 1}/modified.config'

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

        self.tools_used.append({
            'tool': 'search_latest_config',
            'options': options,
            'values': values,
        })

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

        try_dir = f'{self.output_dir}/attempt_{self.attempt}'
        os.makedirs(try_dir, exist_ok=True)

        shutil.copy(self.patch_file, f'{try_dir}/changes.patch')
        
        self.attempt += 1

        self.tools_used.append({
            'tool': 'apply_and_test',
            'define': define,
            'undefine': undefine,
            'success': False
        })

        if not self.kernel.run_klocalizer(try_dir, define, undefine):
            return [f'Error. KLocalizer failed to run. Check the log for details.', self.__tail(f"{try_dir}/klocalizer.log")]

        if not self.kernel.build(f'{try_dir}/modified.config', f'{try_dir}/build.log'):
            return [f'Error. Kernel build failed. Check the log for details.', self.__tail(f"{try_dir}/build.log")]
        
        if not self.kernel.boot(f'{try_dir}/qemu.log'):
            return [f'Error. QEMU boot failed. Check the log for details.', self.__tail(f"{try_dir}/qemu.log")]

        self.succeeded = True  
        self.tools_used[-1]['success'] = True

        return [f'Success. Kernel built and booted successfully. You may finish now.']
        
    def __tail(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return 'No log available.'
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        return '\n'.join(self.__truncate(lines))
    
    def __truncate(self, items: list[str]) -> list[str]:
        
        limit = 20

        if len(items) > limit:
            return items[-limit:] + [f'... (truncated {len(items) - limit} lines)']
        
        return items

    def get_tools(self) -> list[StructuredTool]:
        return [
            StructuredTool.from_function(
                func=self.apply_and_test,
                name='apply_and_test',
                description=self.apply_and_test.__doc__
            ),
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
        ]
