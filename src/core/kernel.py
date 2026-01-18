from src.tools.klocalizer import klocalizer
from src.kernel import KernelRepo, builder
from src.tools.qemu import qemu
from src.config import settings
from src.utils import log
import shutil
import os

class Kernel:

    def __init__(self, kernel_src: str):

        self.kernel_src = kernel_src
        self.repo = KernelRepo(kernel_src)

    @staticmethod
    def get_sample_ends(n: int, start_commit: str | None = None) -> list[str]:

        return KernelRepo.get_sample_ends(n, start_commit)

    def get_kernel_version(self) -> str:
        return self.repo.get_kernel_version()
    
    def create_patch(self, output_dir: str) -> tuple[bool, str | None]:
        
        log.info(f'Creating patch for kernel...')

        success, start_commit = self.repo.make_patch(output_dir)

        if not success:
            log.error('Failed to create patch for kernel.')
            return False, None

        log.success('Patch created successfully.')

        return success, start_commit
    
    def load_config(self, config: str) -> bool:

        log.info(f'Loading configuration for kernel...')

        if not os.path.exists(config):
            log.error(f'Configuration file {config} does not exist.')
            return False
        
        shutil.copy(config, f'{self.repo.path}/.config')

        return True

    def run_klocalizer(self, sample_dir: str, define: list[str] = [], undefine: list[str] = []) -> bool:

        if not os.path.exists(f'{self.repo.path}/.config'):
            log.error('No .config file found in kernel source. Please load a configuration before running KLocalizer.')
            return False

        log.info('Running KLocalizer for kernel...')
        
        if klocalizer.run(self.repo, sample_dir, define, undefine):
            log.success('KLocalizer completed successfully.')
            shutil.copy(f'{self.repo.path}/.config', f'{sample_dir}/modified.config')
            return True
        
        log.error('KLocalizer failed.')

        return False

    def build(self, config: str, log_file: str) -> bool:

        self.load_config(config)

        log.info('Building kernel...')

        built_successfully = builder.build(self.repo, log_file)

        if built_successfully:
            log.success('Kernel built successfully.')
        else:
            log.error('Kernel build failed. Check log for details.')

        return built_successfully

    def boot(self, log_file: str) -> bool:

        log.info('Running QEMU test on kernel...')

        boot_success = qemu.test(self, log_file)

        if boot_success:
            log.success('Kernel booted successfully in QEMU.')
        else:
            log.error('Kernel failed to boot in QEMU. Check log for details.')

        return boot_success
    
    def cleanup(self):
        
        KernelRepo.cleanup(self.kernel_src)
