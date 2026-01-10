from src.utils.log import log_info, log_success, log_error
from src.kernel.repository import KernelRepo
from singleton_decorator import singleton
from src.kernel.kconfig import KConfig
from src.config import config
import subprocess
import os

@singleton
class Builder:

    def make_olddefconfig(self, krepo):

        log_info('Generating olddefconfig...')

        cmd = ['make', 'olddefconfig']
        try:
            result = subprocess.run(cmd, cwd=krepo.path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode != 0:
                log_error('Failed to generate olddefconfig.')
                return False

            return True

        except subprocess.CalledProcessError as e:
            log_error(f'Failed to generate olddefconfig: {e}')
            return False

    def build_kernel(self, krepo, dir):

        log_info('Building the kernel...')

        cwd = krepo.path
        cmd = [
            'make', '-j$(nproc)',
            'LD', 'ld.lld',
            'ARCH', 'x86_64',
            'CROSS_COMPILE', 'ccache x86_64-linux-gnu-',
            'bzImage'
        ]

        try:

            with open(f'{dir}/build.log', 'w') as f:
                result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, text=True, bufsize=1)

                for line in result.stdout:
                    f.write(line)
                    f.flush()

                result.wait()

            log_success('Kernel built successfully.')

            return config.BZIMAGE_PATH, f'{dir}/build.log'        

        except subprocess.CalledProcessError as e:
            log_error(f'Kernel build failed: {e}')
            return None, None
