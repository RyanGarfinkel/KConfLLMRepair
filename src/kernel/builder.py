from src.kernel import KernelRepo, KConfig
from singleton_decorator import singleton
from src.config import settings
from src.utils import log
import subprocess

@singleton
class Builder:

    def build(self, repo: KernelRepo, log_file: str) -> bool:

        cmd = ['bash', settings.BUILD_SCRIPT, repo.path, log_file, str(settings.JOBS)]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return result.returncode == 0
    
builder = Builder()
