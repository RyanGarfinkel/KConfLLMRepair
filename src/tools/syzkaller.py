from singleton_decorator import singleton
from src.config import settings
from src.utils import log
import subprocess

@singleton
class Syzkaller:

    def run(self, kernel_src: str, base_path: str) -> bool:

        cmd = ['bash', settings.scripts.SYZ_KCONF_SCRIPT, kernel_src, base_path, settings.kernel.SYZKCONF_INSTANCE]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            log.error(f'Syzkaller failed with exit code {result.returncode}')
            if result.stderr:
                log.error(f'Stderr: {result.stderr}')

        return result.returncode == 0

syzkaller = Syzkaller()
        