from langchain_core.tools import StructuredTool
from src.kernel import KConfig
from src.models import Sample
from src.core import Kernel
from .rag import RAG
import shutil
import os

class Tools:

    def __init__(self, sample: Sample):

        self.sample = sample
        self.kernel = Kernel(sample.kernel_src)
        self.succeeded = False
        self.attempt = 1
        
        if not os.path.exists(f'{self.sample.output}/attempt_0'):
            raise Exception(f'Output directory {self.sample.output}/attempt_0 does not exist. Please run the initial attempt first.')

        self.base_config = KConfig(f'{self.sample.output}/attempt_0/base.config')

        self.patch_rag = RAG(
            path=f'{self.sample.output}/attempt_{self.attempt - 1}/changes.patch',
            type='patch'
        )

        self.build_log = RAG(
            path=f'{self.sample.output}/attempt_{self.attempt - 1}/build.log',
            type='build'
        )

        self.qemu_log = RAG(
            path=f'{self.sample.output}/attempt_{self.attempt - 1}/qemu.log',
            type='qemu'
        )

        self.used = []

    @property
    def latest_config(self) -> str:
        return f'{self.sample.output}/attempt_{self.attempt - 1}/modified.config'
    
    @property
    def latest_log(self) -> str:

        if os.path.exists(f'{self.sample.output}/attempt_{self.attempt - 1}/qemu.log'):
            with open(f'{self.sample.output}/attempt_{self.attempt - 1}/qemu.log', 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return '\n'.join(self.__truncate(lines))
            
        if os.path.exists(f'{self.sample.output}/attempt_{self.attempt - 1}/build.log'):
            with open(f'{self.sample.output}/attempt_{self.attempt - 1}/build.log', 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return '\n'.join(self.__truncate(lines))
            
        if os.path.exists(f'{self.sample.output}/attempt_0/klocalizer.log'):
            with open(f'{self.sample.output}/attempt_0/klocalizer.log', 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return '\n'.join(self.__truncate(lines))
            
        if os.path.exists(f'{self.sample.output}/attempt_{self.attempt - 1}/changes.patch'):
            with open(f'{self.sample.output}/attempt_{self.attempt - 1}/changes.patch', 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return '\n'.join(self.__truncate(lines))

        return 'No logs or patch files found for the latest attempt.'
    
    @property
    def tools_used(self) -> list[dict]:
        
        used = self.used + self.patch_rag.queries + self.build_log.queries + self.qemu_log.queries
        self.used = []
        self.patch_rag.queries = []
        self.build_log.queries = []
        self.qemu_log.queries = []

        return used

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

        self.used.append({
            'tool': 'search_base_config',
            'options': options,
            'results': values,
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

        config = KConfig(self.latest_config)

        values = []
        for option in options:
            value = config.options.get(option, None)
            if value is not None:
                values.append(f'{option}={value}')
            else:
                values.append(f'{option} not found in KLocalizer config.')

        self.used.append({
            'tool': 'search_latest_config',
            'options': options,
            'results': values,
        })

        return values
    
    def apply_and_test(self, define: list[str], undefine: list[str]) -> list[str]:
        """
        Applies the changes to the kernel configuration using klocalizer and tests the resulting kernel in QEMU.
        The boot log, delta from baseline, and new configuration will be updated after this tool runs.
        ONLY use after gathering sufficient information from the other tools. This tool is expensive and time consuming.

        Args:
            define list[str]: List of configuration options that the klocalizer tool keeps enabled.
            undefine list[str]: List of configuration option names that the klocalizer tool keeps disabled.
        Returns:
            list[str]: A list of messages indicating the result of applying and testing the changes.
        """

        if self.succeeded:
            return ['The kernel has already been successfully built and booted. No further attempts are necessary.']
        
        attempt_dir = f'{self.sample.output}/attempt_{self.attempt}'
        
        if os.path.exists(attempt_dir):
            shutil.rmtree(attempt_dir)

        os.makedirs(attempt_dir, exist_ok=True)
        shutil.copyfile(f'{self.sample.output}/attempt_{self.attempt - 1}/changes.patch', f'{attempt_dir}/changes.patch')

        self.used.append({
            'tool': 'apply_and_test',
            'define': define,
            'undefine': undefine,
            'attempt': self.attempt,
            'klocalizer_succeeded': False,
            'build_succeeded': False,
            'boot_succeeded': False,
        })

        self.build_log.reload(None)
        self.qemu_log.reload(None)
        self.attempt += 1

        self.kernel.load_config(self.base_config.path)
        if not self.kernel.run_klocalizer(attempt_dir, define, undefine):
            return ['KLocalizer failed to apply the configuration changes.']
        
        self.used[-1]['klocalizer_succeeded'] = True

        
        kernel_built = self.kernel.build(f'{attempt_dir}/modified.config', f'{attempt_dir}/build.log')
        self.build_log.reload(f'{attempt_dir}/build.log')
        if not kernel_built:
            return ['Kernel build failed after applying configuration changes. Check build log for details.']

        self.used[-1]['build_succeeded'] = True

        qemu_succeeded = self.kernel.boot(f'{attempt_dir}/qemu.log')
        self.qemu_log.reload(f'{attempt_dir}/qemu.log')
        if not qemu_succeeded:
            return ['Kernel failed to boot in QEMU after applying configuration changes. Check QEMU log for details.']

        self.used[-1]['boot_succeeded'] = True

        self.succeeded = True

        return ['Success. Kernel built and booted successfully. You may finish now.']

    def __truncate(self, lines: list[str]) -> list[str]:

        limit = 20
        if len(lines) > limit:
            return lines[:limit]
        
        return lines
    
    def get_tools(self) -> list[StructuredTool]:
        return [
            self.patch_rag.as_tool(
                name='search_patch',
                desc='Search the patch file for relevant information about code changes made in this attempt.'
            ),
            self.build_log.as_tool(
                name='search_build_log',
                desc='Search the build log for relevant information about build errors and warnings encountered during this attempt.'
            ),
            self.qemu_log.as_tool(
                name='search_qemu_log',
                desc='Search the QEMU log for relevant information about runtime errors and kernel panics encountered during this attempt.'
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
            ),
        ]
