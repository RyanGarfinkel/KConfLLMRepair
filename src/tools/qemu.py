from singleton_decorator import singleton
from src.config import settings
from typing import Literal
import subprocess

@singleton
class Qemu:

    def test(self, kernel_src: str, log_file: str) -> Literal['yes', 'maintenance', 'no']:

        cmd =['bash', settings.scripts.QEMU_TEST_SCRIPT, kernel_src, f'{kernel_src}/{settings.kernel.BZIMAGE}', log_file]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if result.returncode == 0:
            return 'yes'
        elif result.returncode == 2:
            return 'maintenance'
        else:
            return 'no'

qemu = Qemu()
