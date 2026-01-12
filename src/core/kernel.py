from src.kernel import KernelRepo, KConfig, builder
from src.tools.klocalizer import klocalizer
from src.config import settings
import shutil
import os

class Kernel:

    __BASE_CONFIG: KConfig | None = None

    def __init__(self, commit: str):

        self.__load_base_config()
        self.repo = KernelRepo(commit)
        
        Kernel.__BASE_CONFIG.cp(f'{self.repo.path}/.config')

    @property
    def is_built(self) -> bool:
        return os.path.exists(f'{self.repo.path}/{settings.BZIMAGE}')

    @property
    def is_usable(self) -> bool:
        return os.path.exists(self.repo.path)

    def __load_base_config(self):
        if Kernel.__BASE_CONFIG is None:
            Kernel.__BASE_CONFIG = KConfig(f'{settings.BASE_CONFIG}')

    def create_patch(self, output_dir: str, commit_window: int) -> (bool, str | None):
        
        return self.repo.make_patch(output_dir, commit_window)
    
    def run_klocalizer(self, output_dir: str, define: list[str] = [], undefine: list[str] = []) -> bool:

        config = klocalizer.run(self.repo, output_dir, define, undefine)
        
        if config is not None:
            config.cp(f'{output_dir}/klocalizer.config')

        return config is not None

    def build(self, output_dir: str) -> bool:

        return builder.build(self.repo, output_dir)
    
    def cleanup(self):
        
        self.repo.cleanup()

        if os.path.exists(self.repo.path):
            shutil.rmtree(self.repo.path)
