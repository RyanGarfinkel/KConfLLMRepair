from singleton_decorator import singleton
from src.config import settings
import subprocess

@singleton
class KLocalizer:

    def run(self, kernel_src: str, patch: str, log: str, define: list[str] = [], undefine: list[str] = []) -> bool:

        cmd = ['bash', settings.scripts.RUN_KLOCALIZER_SCRIPT, kernel_src, patch, log]

        print('Running KLocalizer with command:', ' '.join(cmd))

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
