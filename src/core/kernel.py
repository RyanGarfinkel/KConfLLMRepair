from src.tools.klocalizer import klocalizer
from src.kernel import KernelRepo, builder
from src.tools import qemu, randconfig
from src.config import settings
from src.utils import log
import shutil
import os

class Kernel:

    def __init__(self, kernel_src: str):

        self.kernel_src = kernel_src
        self.path = kernel_src
        self.src = kernel_src
        self.repo = KernelRepo(kernel_src)

    @property
    def version(self) -> str:

        version = ''
        patchlevel = ''
        sublevel = ''
        extraversion = ''

        with open(f'{self.path}/Makefile', 'r') as f:
            for line in f:
                if line.startswith('VERSION'):
                    version = line.split('=')[1].strip()
                elif line.startswith('PATCHLEVEL'):
                    patchlevel = line.split('=')[1].strip()
                elif line.startswith('SUBLEVEL'):
                    sublevel = line.split('=')[1].strip()
                elif line.startswith('EXTRAVERSION'):
                    extraversion = line.split('=')[1].strip()

        return f'{version}.{patchlevel}.{sublevel}{extraversion}'
    
    def create_patch(self, output_dir: str, start_commit: str | None = None) -> tuple[bool, str | None]:
        
        log.info(f'Creating patch for kernel...')

        success, start_commit = self.repo.make_patch(output_dir, start_commit)

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
    
    def make_rand_config(self, output: str) -> bool:

        log.info('Generating random configuration for kernel...')
    
        if not randconfig.make(self.path, output):
            log.error('Failed to generate random configuration for kernel.')
            return False
        
        log.success('Random configuration generated successfully.')

        return True

    def run_klocalizer(self, patch: str | None, log_path: str, define: list[str] = [], undefine: list[str] = []) -> bool:

        log.info('Running KLocalizer...')

        if not os.path.exists(f'{self.src}/.config'):
            log.error('No .config file found in kernel source. Please load a configuration before running KLocalizer.')
            return False

        if not klocalizer.run(self.src, patch, log_path, define, undefine):
            log.error('KLocalizer failed to run.')
            return False
        
        log.success('KLocalizer completed successfully.')

        return True

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
