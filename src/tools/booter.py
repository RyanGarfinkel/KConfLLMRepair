from singleton_decorator import singleton
from src.config import settings
from src.utils import log
import subprocess
import os

@singleton
class Booter:

    def test(self, kernel: 'Kernel', log_file: str) -> bool:

        cmd =['bash', settings.QEMU_TEST_SCRIPT, kernel.repo.path, f'{kernel.repo.path}/{settings.BZIMAGE}', log_file]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return result.returncode == 0

booter = Booter()
