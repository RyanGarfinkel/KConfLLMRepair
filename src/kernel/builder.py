from src.kernel import KernelRepo, KConfig
from singleton_decorator import singleton
from src.config import settings
from src.utils import log
import subprocess
import os

@singleton
class Builder:

    def __make_olddefconfig(self, repo: KernelRepo) -> bool:

        log.info(f'Generating olddefconfig for commit {repo.commit}...')

        cmd = ['make', 'olddefconfig']
        try:
            subprocess.run(cmd, cwd=repo.path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log.success(f'olddefconfig generated successfully for commit {repo.commit}.')

            return True

        except subprocess.CalledProcessError as e:
            log.error(f'Failed to generate olddefconfig for commit {repo.commit}: {e}')
            return False

    def build(self, repo: KernelRepo, output_dir: str) -> bool:

        if not self.__make_olddefconfig(repo):
            return False

        log.info(f'Starting kernel build process for {repo.commit}...')

        cmd = [
            'make', f'-j{settings.JOBS}',
            'LD', 'ld.lld',
            'ARCH', 'x86_64',
            'CROSS_COMPILE', 'ccache x86_64-linux-gnu-',
            'bzImage'
        ]

        log_file = f'{output_dir}/build.log'

        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(log_file, 'w') as f:
                result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=repo.path, text=True, bufsize=1)

                for line in result.stdout:
                    f.write(line)
                    f.flush()

                result.wait()

            if result.returncode != 0:
                log.error(f'Kernel build failed for commit {repo.commit}. Check build.log for details.')
                return False

            if not os.path.exists(f'{repo.path}/{settings.BZIMAGE}'):
                log.error(f'Kernel build failed for commit {repo.commit}. Check build.log for details.')
                return False

            log.success(f'Kernel built successfully for commit {repo.commit}.')

            return True
        except subprocess.CalledProcessError as e:
            log.error(f'Kernel build failed for commit {repo.commit}: {e}')
            return False

builder = Builder()
