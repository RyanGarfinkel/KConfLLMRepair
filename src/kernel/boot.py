from src.utils.log import log_info, log_success, log_error
from dotenv import load_dotenv
from src.config import config
import subprocess
import os

def does_boot(bzImage, dir):

    log_info('Running QEMU test...')
    log_info(f'You can view the logs at {dir}/qemu.log')

    cmd = ['sh', config.QEMU_TEST_SCRIPT, bzImage, dir]
    process = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if process.returncode != 0:
        log_error('QEMU test failed.')
    else:
        log_success('Sample booted successfully in QEMU.')

    return process.returncode == 0
