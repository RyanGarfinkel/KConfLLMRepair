from singleton_decorator import singleton
from src.config import settings
from typing import Literal
import subprocess
import json
import os

@singleton
class Koverage:

    def run(self, kernel_src: str, config: str, patch: str, log: str) -> tuple[Literal['success', 'error'], float | None, str | None]:

        cmd = ['bash', settings.scripts.RUN_KOVERAGE_SCRIPT, kernel_src, config, patch, log, settings.kernel.ARCH]

        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        if result.returncode != 0:
            return 'error', None, None

        output_path = f'{os.path.dirname(log)}/coverage_report.json'
        if not os.path.exists(output_path):
            return 'success', None, None

        return 'success', self.__compute_coverage(output_path), output_path

    def __compute_coverage(self, path: str) -> float | None:

        if not os.path.exists(path):
            return None

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        included = 0
        total = 0

        for section in ('sourcefile_loc', 'headerfile_loc'):
            for lines in data.get(section, {}).values():
                total += len(lines)
                included += sum(1 for _, status in lines if status == 'INCLUDED')

        return included / total if total > 0 else None

koverage = Koverage()
