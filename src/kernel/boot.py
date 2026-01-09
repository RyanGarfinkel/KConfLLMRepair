from src.utils.log import log_info, log_success, log_error
from dotenv import load_dotenv
import subprocess
import os

load_dotenv()

_QEMU_TEST_SCRIPT = os.getenv('QEMU_TEST_SCRIPT')
if not _QEMU_TEST_SCRIPT:
    raise EnvironmentError('QEMU_TEST_SCRIPT not set.')

def does_boot(bzImage, dir):

    log_info('Running QEMU test...')
    log_info(f'You can view the logs at {dir}/qemu.log')

    cmd = ['sh', _QEMU_TEST_SCRIPT, bzImage, dir]
    process = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if process.returncode != 0:
        log_error('QEMU test failed.')
    else:
        log_success('Sample booted successfully in QEMU.')

    return process.returncode == 0
