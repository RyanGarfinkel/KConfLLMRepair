from singleton_decorator import singleton
from src.config import settings
from src.utils import log
import subprocess
import os

@singleton
class Booter:

    def test(self, kernel: 'Kernel', output_dir: str) -> bool:

        log.info(f'Running QEMU test on {kernel.repo.commit}...')

        cmd =['sh', settings.QEMU_TEST_SCRIPT, kernel.repo.path, f'{kernel.repo.path}/{settings.BZIMAGE}', output_dir]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if result.returncode != 0:
            log.error(f'QEMU test failed for commit {kernel.repo.commit}.')
        else:
            log.success(f'Sample booted successfully in QEMU for commit {kernel.repo.commit}.')

        return result.returncode == 0

booter = Booter()
