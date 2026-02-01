from singleton_decorator import singleton
from src.config import settings
import subprocess

@singleton
class Qemu:

    def test(self, kernel: 'Kernel', log_file: str) -> bool:

        cmd =['bash', settings.scripts.QEMU_TEST_SCRIPT, kernel.repo.path, f'{kernel.repo.path}/{settings.kernel.BZIMAGE}', log_file]
        print(f'Running QEMU test with command:\n{" ".join(cmd)}')
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return result.returncode == 0

qemu = Qemu()
