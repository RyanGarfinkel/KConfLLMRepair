from src.tools.klocalizer import klocalizer
from src.kernel import KernelRepo, builder
from src.tools.booter import booter
from src.config import settings
from src.utils import log
import shutil
import os

class Kernel:

    def __init__(self, commit: str):

        self.repo = KernelRepo(commit)

    def create_patch(self, output_dir: str) -> tuple[bool, str | None]:
        
        log.info(f'Creating patch for kernel {self.repo.commit}...')

        success, start_commit = self.repo.make_patch(output_dir)

        if not success:
            log.error('Failed to create patch for kernel.')
            return False, None

        log.success('Patch created successfully.')

        return success, start_commit
    
    def load_config(self, config: str) -> bool:

        log.info(f'Loading configuration for kernel {self.repo.commit}...')

        if not os.path.exists(config):
            log.error(f'Configuration file {config} does not exist.')
            return False
        
        shutil.copy(config, f'{self.repo.path}/.config')

        return True

    def run_klocalizer(self, sample_dir: str, define: list[str] = [], undefine: list[str] = []) -> bool:

        log.info(f'Running KLocalizer for kernel {self.repo.commit}...')

        self.load_config(settings.BASE_CONFIG)
        
        if klocalizer.run(self.repo, sample_dir, define, undefine):
            log.success(f'KLocalizer completed successfully.')
            return True
        
        log.error(f'KLocalizer failed.')

        return False

    def build(self, config: str, log_file: str) -> bool:

        self.load_config(config)

        log.info(f'Building kernel {self.repo.commit}...')

        built_successfully = builder.build(self.repo, log_file)

        if built_successfully:
            log.success('Kernel built successfully.')
        else:
            log.error('Kernel build failed. Check log for details.')

        return built_successfully

    def boot(self, log_file: str) -> bool:

        log.info(f'Running QEMU test on kernel {self.repo.commit}...')

        boot_success = booter.test(self, log_file)

        if boot_success:
            log.success('Kernel booted successfully in QEMU.')
        else:
            log.error('Kernel failed to boot in QEMU. Check log for details.')

        return boot_success
    
    def cleanup(self):
        
        self.repo.cleanup()

        if os.path.exists(self.repo.path):
            shutil.rmtree(self.repo.path)
