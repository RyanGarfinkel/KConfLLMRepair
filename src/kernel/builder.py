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
        self.repo = KernelRepo()
        self._SYZKALLER_PATH = '/home/ubuntu/syzkaller'
        self._KVM_CONFIG = 'kernel/configs/kvm_guest.config'

    def build_patch(self, output_path):

        log_info('Fetching kernel patch...')

        commits = self.repo.get_commit_window()

        start = commits[-1]
        end = commits[0]

        diff = self.repo.diff(start, end)

        with open(output_path, 'w') as f:
            f.write(diff)

        log_success(f'Kernel patch saved to {output_path}.')

        return start, end

    def _make_olddefconfig(self, arch='x86_64') -> bool:
        
        log_info('Generating olddefconfig...')

        result = subprocess.run(f'make olddefconfig ARCH={arch} CROSS_COMPILE={arch}-linux-gnu- LD=ld.lld', shell=True, check=True, cwd=kernel_src)
        if result.returncode != 0:
            log_error('Failed to generate olddefconfig.')
            return False
        
        log_success('olddefconfig generated successfully.')

        return True
    
    def build_kernel(self, arch='x86_64'):

        self._make_olddefconfig()

        log_info('Building the kernel...')

        result = subprocess.run(f'make -j$(nproc) LD=ld.lld ARCH={arch} CROSS_COMPILE="ccache {arch}-linux-gnu-" bzImage', shell=True, check=True, cwd=kernel_src)
        if result.returncode != 0:
            raise Exception('Kernel build failed.')
        
        log_success('Kernel built successfully.')

        return _BZIMAGE_PATH
