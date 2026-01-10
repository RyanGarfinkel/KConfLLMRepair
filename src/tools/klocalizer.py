from src.utils.log import log_info, log_error, log_success
from singleton_decorator import singleton
from src.kernel.kconfig import KConfig
from src.config import config
import subprocess
import os

@singleton
class KLocalizer():

    def repair(self, kernel_src, dir, define=[], undefine=[]):

        log_info('Starting klocalizer repair...')

        patch = f'{dir}/changes.patch'

        cmd = [
            'klocalizer',
            '--superc-linux-script', config.SUPERC_PATH,
            '--include-mutex', patch,
            '--cross-compiler', 'gcc',
            '--arch', config.ARCH   
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
            
            if result.returncode != 0:
                log_error(f'klocalizer repair failed with return code {result.returncode}. Check klocalizer.log for details.')
                return None
            
            log_success('klocalizer repair completed.')

            klocalizer_config = KConfig(f'{kernel_src}/0-{config.ARCH}.config')
            klocalizer_config.mv(f'{kernel_src}/.config')

            return klocalizer_config
        except subprocess.CalledProcessError as e:
            log_error(f'klocalizer repair failed: {e}')
            return None
