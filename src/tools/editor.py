from singleton_decorator import singleton
from src.config import settings
from typing import Literal
import subprocess

@singleton
class ConfigEditor:

    def apply(self, kernel_src: str, log: str, define: list[str] = [], undefine: list[str] = []) -> Literal['success', 'no-satisfying-constraints', 'error']:

        if set(define) & set(undefine):
            return 'no-satisfying-constraints'

        cmd = ['bash', settings.scripts.APPLY_OPTIONS_SCRIPT, kernel_src, log, settings.kernel.ARCH]

        for opt in define:
            cmd.extend(['--enable', opt])

        for opt in undefine:
            cmd.extend(['--disable', opt])

        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        if result.returncode == 0:
            return 'success'
        return 'error'

config_editor = ConfigEditor()
