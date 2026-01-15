from src.kernel import KernelRepo, KConfig
from singleton_decorator import singleton
from src.config import settings
from src.utils import log
import subprocess
import os

@singleton
class KLocalizer:

    def run(self, repo: KernelRepo, sample_dir: str, define: list[str] = [], undefine: list[str] = []) -> bool:

        cmd = ['bash', settings.scripts.RUN_KLOCALIZER_SCRIPT, repo.path, f'{sample_dir}/changes.patch', f'{sample_dir}/klocalizer.log']

        for opt in define:
            cmd.extend(['--define', opt])
            
        for opt in undefine:
            cmd.extend(['--undefine', opt])

        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return result.returncode == 0

klocalizer = KLocalizer()
