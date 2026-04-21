from singleton_decorator import singleton
from src.config import settings
from typing import Literal
import subprocess
import os

@singleton
class KLocalizer:

    def run(self, kernel_src: str, log: str, define: list[str] = [], undefine: list[str] = []) -> Literal['success', 'no-satisfying-constraints', 'error']:

        if set(define) & set(undefine):
            return 'no-satisfying-constraints'

        parent = os.path.dirname(log)

        with open(f'{parent}/constraints.txt', 'w', encoding='utf-8') as f:
            for option in define:
                f.write(f'{option}\n')

            for option in undefine:
                f.write(f'!{option}\n')

        cmd = ['bash', settings.scripts.RUN_KLOCALIZER_SCRIPT, kernel_src, f'{parent}/constraints.txt', log, settings.kernel.ARCH]

        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        if result.returncode == 0:
            return 'success'
        if result.returncode == 11:
            return 'no-satisfying-constraints'
        return 'error'

    def run_patch(self, kernel_src: str, patch: str, log: str, define: list[str] = [], undefine: list[str] = []) -> Literal['success', 'no-satisfying-constraints', 'error']:

        cmd = ['bash', settings.scripts.RUN_KLOCALIZER_PATCH_SCRIPT, kernel_src, patch, log, settings.kernel.ARCH]

        for opt in define:
            cmd.extend(['--define', opt])

        for opt in undefine:
            cmd.extend(['--undefine', opt])

        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        if result.returncode == 0:
            return 'success'
        if result.returncode == 11:
            return 'no-satisfying-constraints'
        return 'error'

klocalizer = KLocalizer()
