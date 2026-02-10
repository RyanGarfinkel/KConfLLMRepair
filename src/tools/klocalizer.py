from singleton_decorator import singleton
from src.config import settings
import subprocess
import shutil
import os

@singleton
class KLocalizer:

    def run(self, kernel_src: str, patch: str | None, log: str, define: list[str] = [], undefine: list[str] = []) -> bool:
        
        if not patch:
            print('correct place')
            with open(f'{kernel_src}/constraints.txt', 'w') as f:
                for option in define:
                    f.write(option + '\n')

                for option in undefine:
                    f.write(f'!{option}\n')
            
            cmd = ['bash', settings.scripts.RUN_KLOCALIZER_CONSTRAINTS_SCRIPT, kernel_src, f'{kernel_src}/constraints.txt', log]
        else:
            cmd = ['bash', settings.scripts.RUN_KLOCALIZER_SCRIPT, kernel_src, patch, log]

            for opt in define:
                cmd.extend(['--define', opt])
                
            for opt in undefine:
                cmd.extend(['--undefine', opt])

        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            if result.stdout:
                print('KLocalizer output:\n', result.stdout)
            
            if result.stderr:
                print('KLocalizer error output:\n', result.stderr)
        
        return result.returncode == 0

klocalizer = KLocalizer()
