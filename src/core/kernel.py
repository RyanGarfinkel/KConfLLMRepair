from src.models import BuildResult, BootResult, KlocalizerResult, KoverageResult
from src.tools import klocalizer, qemu, koverage
from src.kernel import randconfig
from src.config import settings
from src.kernel import builder
from src.utils import log
from git import Repo
import shutil
import time
import os

class Kernel:

    def __init__(self, src: str):

        if not os.path.exists(src):
            raise ValueError(f'Kernel source path does not exist: {src}')

        self.src = src
        self.__version: str | None = None

    @property
    def version(self) -> str:

        if self.__version:
            return self.__version

        version = ''
        patchlevel = ''
        sublevel = ''
        extraversion = ''

        with open(f'{self.src}/Makefile', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('VERSION'):
                    version = line.split('=')[1].strip()
                elif line.startswith('PATCHLEVEL'):
                    patchlevel = line.split('=')[1].strip()
                elif line.startswith('SUBLEVEL'):
                    sublevel = line.split('=')[1].strip()
                elif line.startswith('EXTRAVERSION'):
                    extraversion = line.split('=')[1].strip()

        self.__version = f'{version}.{patchlevel}.{sublevel}{extraversion}'
        return self.__version

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

        try:
            repo = Repo(self.src)
            diff = repo.git.diff(f'HEAD~{settings.runtime.COMMIT_WINDOW}..HEAD')

            with open(path, 'w', encoding='utf-8') as f:
                f.write(diff)

            return True
        except Exception as e:
            log.error(f'Failed to create patch: {e}')
            return False
    
    def make_rand_config(self, path: str, seed: int) -> bool:

        log.info('Generating random configuration...')

        if not randconfig.make(self.src, path, seed):
            log.error('Randconfig failed to generate a base configuration.')
            return False
        
        log.success('Random configuration generated successfully.')

        return True
    
    def run_klocalizer(self, dir: str, config: str, define: list[str] = [], undefine: list[str] = [], patch: str | None = None) -> KlocalizerResult:

        log_path = f'{dir}/klocalizer.log'

        if not self.load_config(config):
            return KlocalizerResult(status='error', log=log_path)

        log.info('Running KLocalizer...')

        start = time.time()

        # if patch is not None:
        #     status = klocalizer.run_patch(self.src, patch, log_path, define, undefine)
        # else:
        #     status = klocalizer.run(self.src, log_path, define, undefine)

        status = klocalizer.run(self.src, log_path, define, undefine)

        klocalizer_time = time.time() - start

        if status == 'success':
            log.success('KLocalizer completed successfully.')
        elif status == 'no-satisfying-constraints':
            log.warning('KLocalizer found no satisfying constraints.')
        else:
            log.error('KLocalizer failed.')

        return KlocalizerResult(status=status, log=log_path, klocalizer_time=klocalizer_time)

    def build(self, dir: str, config: str) -> BuildResult:

        log_path = f'{dir}/build.log'

        if not self.load_config(config):
            return BuildResult(ok=False, log=log_path)

        log.info('Building kernel...')

        start = time.time()
        ok = builder.build(self.src, log_path)
        build_time = time.time() - start

        if not ok:
            log.error('Build failed. Check log for details.')
            return BuildResult(ok=False, log=log_path, build_time=build_time, summary=self.__extract_build_summary(log_path))

        log.success('Build completed successfully.')

        return BuildResult(ok=True, log=log_path, build_time=build_time)

    def boot(self, dir: str) -> BootResult:

        log.info('Running QEMU test on kernel...')

        log_path = f'{dir}/boot.log'

        if not os.path.exists(f'{self.src}/{settings.kernel.BZIMAGE}'):
            log.error('Kernel binary not found. Please build the kernel before booting.')
            return BootResult(status='no', log=log_path)

        start = time.time()
        status = qemu.test(self.src, log_path)
        boot_time = time.time() - start

        if status == 'yes':
            log.success('QEMU test completed successfully.')
        elif status == 'maintenance':
            log.warning('QEMU test returned maintenance mode.')
        elif status == 'panic':
            log.error('Kernel panic detected.')
        elif status == 'timeout':
            log.error('Boot timed out.')
        else:
            log.error('QEMU process failed. Check log for details.')

        return BootResult(status=status, log=log_path, boot_time=boot_time, summary=self.__extract_boot_summary(log_path, status))

    def run_koverage(self, dir: str, patch: str) -> KoverageResult:

        log_path = f'{dir}/koverage.log'
        config = f'{self.src}/.config'

        if not os.path.exists(config):
            log.error('Cannot calculate patch coverage. No configuration file found.')
            return KoverageResult(status='error', log=log_path)

        log.info('Calculating patch coverage...')

        start = time.time()
        status, coverage, coverage_report = koverage.run(self.src, config, patch, log_path)
        koverage_time = time.time() - start

        if status == 'success' and coverage is not None:
            log.success(f'Coverage calculated: {(coverage * 100):.2f}%')
        elif status == 'success':
            log.warning('Coverage calculated, but patch has no coverable lines.')
        else:
            log.error('Koverage failed. Check log for details.')

        return KoverageResult(status=status, coverage=coverage, coverage_report=coverage_report, log=log_path, koverage_time=koverage_time, summary=self.__extract_coverage_summary(status, coverage))

    def __extract_coverage_summary(self, status: str, coverage: float | None) -> str | None:

        if status == 'error':
            return 'Patch coverage could not be measured (koverage failed).'

        if coverage is None:
            return 'The patch has no coverable lines under koverage.'

        target_pct = settings.runtime.MIN_COVERAGE * 100
        return f'The config covers {(coverage * 100):.1f}% of the patch (target: >{target_pct:.1f}%).'

    def __extract_build_summary(self, log_path: str) -> str | None:
        try:
            with open(log_path, encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except OSError:
            return None

        start = max(0, len(lines) - 50)
        return ''.join(f'{start + j}: {l}' for j, l in enumerate(lines[start:])).strip() or None

    def __extract_boot_summary(self, log_path: str, status: str) -> str | None:
        try:
            with open(log_path, encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except OSError:
            return None

        if not lines:
            return None

        if status == 'panic':
            for i, line in enumerate(lines):
                if 'Kernel panic' in line:
                    return ''.join(f'{i + j}: {l}' for j, l in enumerate(lines[i:i + 25])).strip()
            return None

        if status == 'timeout':
            start = max(0, len(lines) - 50)
            return ''.join(f'{start + j}: {l}' for j, l in enumerate(lines[start:])).strip()

        if status == 'maintenance':
            failed = [(i, l) for i, l in enumerate(lines) if 'FAILED' in l]
            return ''.join(f'{i}: {l}' for i, l in failed[:20]).strip() or None

        return None
