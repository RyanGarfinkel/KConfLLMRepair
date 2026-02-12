from singleton_decorator import singleton
from src.config import settings
from src.utils import log
import subprocess

@singleton
class RandConfig:

    def make(self, kernel_src: str, output: str) -> bool:

        cmd = ['bash', settings.scripts.RAND_CONFIG_SCRIPT, kernel_src, output]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            log.error(f'Syzkaller failed with exit code {result.returncode}')
            if result.stderr:
                log.error(f'Stderr: {result.stderr}')

        return result.returncode == 0

randconfig = RandConfig()
        