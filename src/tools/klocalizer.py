from singleton_decorator import singleton
from src.config import settings
from src.utils import file_lock
import subprocess
import os

@singleton
class KLocalizer:

    def run(self, kernel_src: str, log: str, define: list[str] = [], undefine: list[str] = []) -> bool:
        
        parent = os.path.dirname(log)

        with file_lock:
            with open(f'{parent}/constraints.txt', 'w') as f:
                for option in define:
                    f.write(option + '\n')

                for option in undefine:
                    f.write(f'!{option}\n')
            
        cmd = ['bash', settings.scripts.RUN_KLOCALIZER_SCRIPT, kernel_src, f'{parent}/constraints.txt', log]

        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return result.returncode == 0

klocalizer = KLocalizer()
