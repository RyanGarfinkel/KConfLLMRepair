from src.config import superc_linux_script_path
from src.utils.log import log_info, log_error, log_success
from singleton_decorator import singleton
from src.kernel.kconfig import KConfig
from dotenv import load_dotenv
import subprocess
import os

load_dotenv()

_ARCH = os.getenv('ARCH')
if not _ARCH:
    raise EnvironmentError('ARCH not set.')

@singleton
class KLocalizer():

    def __init__(self):

        self.klocalizer_path = '/home/ubuntu/.local/bin/klocalizer'
        self.superc_path = '/home/ubuntu/.local/bin/superc_linux.sh'

    def repair(self, kernel_src, dir, define=[], undefine=[]):

        log_info('Starting klocalizer repair...')

        patch = f'{dir}/changes.patch'

        cmd = [
            'klocalizer',
            '--superc-linux-script', self.superc_path,
            '--include-mutex', patch,
            '--cross-compiler', 'gcc',
            '--arch', _ARCH   
        ]

        cmd.extend([f'--define {opt}' for opt in define])
        cmd.extend([f'--undefine {opt}' for opt in undefine])

        try:

            with open(f'{dir}/klocalizer.log', 'w') as f:
                result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=kernel_src, text=True, bufsize=1)

                for line in result.stdout:
                    f.write(line)
                    f.flush()
                
                result.wait()
            
            log_success('klocalizer repair completed.')

            config = KConfig(f'{kernel_src}/0-{_ARCH}.config')
            config.mv(f'{kernel_src}/.config')

            return config
        except subprocess.CalledProcessError as e:
            log_error(f'klocalizer repair failed: {e}')
            return None
