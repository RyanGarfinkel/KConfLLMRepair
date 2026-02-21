from src.tools import klocalizer, qemu, randconfig
from src.config import settings
from src.kernel import builder
from typing import Literal
from src.utils import log
from git import Repo
import shutil
import os

class Kernel:

    def __init__(self, src: str):
        
        if not os.path.exists(src):
            raise ValueError(f'Kernel source path does not exist: {src}')
        
        self.src = src

    @property
    def version(self) -> str:
    
        version = ''
        patchlevel = ''
        sublevel = ''
        extraversion = ''

        with open(f'{self.src}/Makefile', 'r') as f:
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

    def load_config(self, path: str) -> bool:

        log.info(f'Loading config into kernel: {path}')

        if not os.path.basename(path).endswith('.config'):
            log.error(f'Provided config file is not a .config file: {path}')
            return False

        if not os.path.exists(path):
            log.error(f'Config file does not exist: {path}')
            return False
        
        shutil.copy(path, f'{self.src}/.config')

        return True

    def make_patch(self, path: str) -> bool:

        repo = Repo(self.src)

        diff = repo.git.diff(f'HEAD~{settings.runtime.COMMIT_WINDOW}..HEAD')
        
        with open(path, 'w') as f:
            f.write(diff)

        return True
    
    def make_rand_config(self, path: str) -> bool:

        log.info('Generating random configuration...')

        if not randconfig.make(self.src, path):
            log.error('Randconfig failed to generate a base configuration.')
            return False
        
        log.success('Random configuration generated successfully.')

        return True
    
    def run_klocalizer(self, log_path: str, define: list[str] = [], undefine: list[str] = []) -> bool:

        log.info('Running KLocalizer...')
        
        if not os.path.exists(f'{self.src}/.config'):
            log.error('No .config file found in kernel source. Please load a configuration before running KLocalizer.')
            return False

        if not klocalizer.run(self.src, log_path, define, undefine):
            log.error('KLocalizer failed to run.')
            return False
        
        log.success('KLocalizer completed successfully.')

        return True
    
    def build(self, path: str) -> bool:
        
        log.info('Building kernel...')

        if not os.path.exists(f'{self.src}/.config'):
            log.error('Config file not found in kernel source. Please load a configuration before building.')
            return False

        if not builder.build(self.src, path):
            log.error('Build failed. Check log for details.')
            return False
        
        log.success('Build completed successfully.')

        return True
    
    def boot(self, path: str) -> Literal['yes', 'maintenance', 'no']:

        log.info('Running QEMU test on kernel...')

        if not os.path.exists(f'{self.src}/{settings.kernel.BZIMAGE}'):
            log.error('Kernel binary not found. Please build the kernel before booting.')
            return 'no'
        
        result = qemu.test(self.src, path)
        if result == 'no':
            log.error('QEMU test failed. Check log for details.')
            return 'no'
        elif result == 'maintenance':
            log.warning('QEMU test returned maintenance mode.')
            return 'maintenance'

        log.success('QEMU test completed successfully.')

        return 'yes'
