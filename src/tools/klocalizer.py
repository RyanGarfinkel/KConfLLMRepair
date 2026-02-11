from singleton_decorator import singleton
from src.config import settings
from src.utils import file_lock
import subprocess

@singleton
class KLocalizer:

    def run(self, kernel_src: str, log: str, define: list[str] = [], undefine: list[str] = []) -> bool:
        
        with file_lock:
            with open(f'{kernel_src}/constraints.txt', 'w') as f:
                for option in define:
                    f.write(option + '\n')

                for option in undefine:
                    f.write(f'!{option}\n')
            
        cmd = ['bash', settings.scripts.RUN_KLOCALIZER_CONSTRAINTS_SCRIPT, kernel_src, f'{kernel_src}/constraints.txt', log]

        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            if result.stdout:
                print('KLocalizer output:\n', result.stdout)
            
            if result.stderr:
                print('KLocalizer error output:\n', result.stderr)
        
        return result.returncode == 0

klocalizer = KLocalizer()
