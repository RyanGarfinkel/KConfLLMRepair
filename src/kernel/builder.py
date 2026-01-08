from src.utils.log import log_info, log_success, log_error
from src.kernel.repository import KernelRepo
from singleton_decorator import singleton
from src.kernel.kconfig import KConfig
from src.config import kernel_src
import subprocess
import os

_BZIMAGE_PATH = 'arch/x86/boot/bzImage'

@singleton
class Builder:

    def __init__(self):

        self._BZIMAGE_PATH = 'arch/x86/boot/bzImage'

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

            return self._BZIMAGE_PATH            

        except subprocess.CalledProcessError as e:
            log_error(f'Kernel build failed: {e}')
            return None



# @singleton
# class Builder:

#     def __init__(self):
#         self.repo = KernelRepo()
#         self._SYZKALLER_PATH = '/home/ubuntu/syzkaller'
#         self._KVM_CONFIG = 'kernel/configs/kvm_guest.config'

#     def build_patch(self, output_path):

#         log_info('Fetching kernel patch...')

#         commits = self.repo.get_commit_window()

#         start = commits[-1]
#         end = commits[0]

#         diff = self.repo.diff(start, end)

#         with open(output_path, 'w') as f:
#             f.write(diff)

#         log_success(f'Kernel patch saved to {output_path}.')

#         return start, end

#     def _make_olddefconfig(self, arch='x86_64') -> bool:
        
#         log_info('Generating olddefconfig...')

#         result = subprocess.run(f'make olddefconfig ARCH={arch} CROSS_COMPILE={arch}-linux-gnu- LD=ld.lld', shell=True, check=True, cwd=kernel_src)
#         if result.returncode != 0:
#             log_error('Failed to generate olddefconfig.')
#             return False
        
#         log_success('olddefconfig generated successfully.')

#         return True
    
#     def build_kernel(self, arch='x86_64'):

#         self._make_olddefconfig()

#         log_info('Building the kernel...')

#         result = subprocess.run(f'make -j$(nproc) LD=ld.lld ARCH={arch} CROSS_COMPILE="ccache {arch}-linux-gnu-" bzImage', shell=True, check=True, cwd=kernel_src)
#         if result.returncode != 0:
#             raise Exception('Kernel build failed.')
        
#         log_success('Kernel built successfully.')

#         return _BZIMAGE_PATH
