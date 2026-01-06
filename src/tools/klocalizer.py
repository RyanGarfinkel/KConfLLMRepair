from src.config import kernel_src, superc_linux_script_path
from src.utils.log import log_info, log_error, log_success
from singleton_decorator import singleton
from src.kernel.kconfig import KConfig
import subprocess

@singleton
class KLocalizer():

    def __init__(self):

        self.klocalizer_path = '/home/ubuntu/.local/bin/klocalizer'
        self.superc_path = '/home/ubuntu/.local/bin/superc_linux.sh'

    def repair(self, patch, define=[], undefine=[], arch='x86_64'):

        log_info('Starting klocalizer repair...')

        define_opts = ' '.join([f'--define {opt}' for opt in define]) if define else ''
        undefine_opts = ' '.join([f'--undefine {opt}' for opt in undefine]) if undefine else ''

        cmd = f'{self.klocalizer_path} \
            --superc-linux-script {self.superc_path} \
            --include-mutex {patch} \
            --cross-compiler gcc \
            --arch {arch} \
            {define_opts} \
            {undefine_opts}'

        result = subprocess.run(cmd, shell=True, check=True, cwd=kernel_src)
        if result.returncode != 0:
            log_error(f'klocalizer repair failed: {result.stderr}')
            return None
        
        log_success('klocalizer repair completed.')

        return KConfig(f'{kernel_src}/0-{arch}.config')