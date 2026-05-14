from singleton_decorator import singleton
from src.config import settings
from typing import Literal
import subprocess

@singleton
class Qemu:

    def test(self, kernel_src: str, log_file: str) -> Literal['yes', 'maintenance', 'panic', 'timeout', 'no']:

        cmd = ['bash', settings.scripts.QEMU_TEST_SCRIPT, kernel_src, f'{kernel_src}/{settings.kernel.BZIMAGE}', log_file, settings.kernel.ARCH, settings.kernel.DEBIAN_IMG]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        if result.returncode == 0:
            return 'yes'
        if result.returncode == 2:
            return 'maintenance'

        try:
            with open(log_file, encoding='utf-8', errors='replace') as f:
                log = f.read()
            if 'Kernel panic' in log:
                return 'panic'
            if log.strip():
                return 'timeout'
        except OSError:
            pass

        return 'no'

qemu = Qemu()
