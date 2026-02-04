from singleton_decorator import singleton
from src.settings import settings
from src.utils import log
import subprocess
import os

@singleton
class DiffConfig:

    def compare(self, base_config: str, modified_config: str) -> tuple[list[str], int]:

        diffconfig_path = os.path.join(settings.kernel.KERNEL_SRC, settings.kernel.DIFFCONFIG)

        cmd = [
            diffconfig_path,
            base_config,
            modified_config
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            log.error('DiffConfig failed to compare configurations.')
            return [], -1

        diff_lines = result.stdout.strip().split('\n')
        num_differences = len(diff_lines)

        return diff_lines, num_differences

diffconfig = DiffConfig()
