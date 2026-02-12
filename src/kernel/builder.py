from singleton_decorator import singleton
from src.config import settings
import subprocess

@singleton
class Builder:

    def build(self, kernel_src: str, log_file: str) -> bool:

        cmd = ['bash', settings.scripts.BUILD_SCRIPT, kernel_src, log_file, str(settings.runtime.JOBS)]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return result.returncode == 0
    
builder = Builder()
