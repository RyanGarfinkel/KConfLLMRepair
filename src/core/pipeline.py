import os

from src.kernel.kconfig import KConfig
from src.kernel.repository import KernelRepo
from src.tools.syzkaller import Syzkaller
from src.tools.klocalizer import KLocalizer
from src.config import kernel_src
from src.kernel.builder import Builder
from src.kernel.repository import KernelRepo
from src.kernel.boot import KernelBooter
from src.utils.log import log_info, log_success, log_error
from dotenv import load_dotenv
import subprocess
import os

load_dotenv()

_BASE_CONFIG = os.getenv('BASE_CONFIG')
if not _BASE_CONFIG:
    raise EnvironmentError('BASE_CONFIG not set.')

if not os.path.exists(_BASE_CONFIG):
    raise FileNotFoundError(f'Base config file not found at {_BASE_CONFIG}')

_QEMU_TEST_SCRIPT = os.getenv('QEMU_TEST_SCRIPT')
if not _QEMU_TEST_SCRIPT:
    raise EnvironmentError('QEMU_TEST_SCRIPT not set.')

cols = ['start_commit', 'end_commit', 'patch_path', 'klocalizer_config_path', 'qemu_boot_success']

def generate_sample(dir, commit):

    os.makedirs(dir, exist_ok=True)
    result = []

    repo = KernelRepo(commit)
    klocalizer = KLocalizer()
    builder = Builder()

    # Build the patch
    start, end, patch = repo.build_patch(dir)
    result.extend([start, end, patch])

    # Copy base config
    base_config = KConfig(_BASE_CONFIG)
    base_config.cp(f'{repo.path}/.config')

    # Run KLocalizer
    klocalizer_config = klocalizer.repair(repo.path, dir)
    if klocalizer_config is None:
        log_error('KLocalizer repair failed. Aborting sample generation.')
        return result
    
    if not builder.make_olddefconfig(repo):
        return result

    klocalizer_config.cp(f'{dir}/klocalizer.config')
    result.append(f'{dir}/klocalizer.config')

    # Buid the kernel with updated config
    bzImg = builder.build_kernel(repo, dir)
    if not bzImg:
        return result

    # QEMU test
    log_info('Running QEMU test...')
    log_info(f'You can view the logs at {dir}/qemu.log')

    cmd = ['sh', _QEMU_TEST_SCRIPT, bzImg, dir]
    process = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if process.returncode != 0:
        log_error('QEMU test failed.')
        result.append(False)
    else:
        log_success('Sample booted successfully in QEMU.')
        result.append(True)

    # Finish
    log_info('Sample generation complete.')

    return result

def generate_single_baseline(dir):

    res = []

    builder = Builder()
    repo = KernelRepo()

    img_path = os.getenv('BULLSEYE_IMG')

    log_info('Cleaning kernel repository...')
    repo.clean()
    
    # Get Patch
    start, end = builder.build_patch(f'{dir}/changes.patch')
    repo.checkout(end)

    res.append(start)
    res.append(end)
    res.append(f'{dir}/changes.patch')

    # Get Base Config from Syzkaller
    syzkaller = Syzkaller()
    wasBuilt = syzkaller.build_for(end)
    if not wasBuilt:
        print('Syzkaller build failed. Aborting sample generation.')
        return res
    
    base_config = syzkaller.generate_base_config()
    if base_config is None:
        print('Failed to generate base syzkaller config. Aborting sample generation.')
        return res

    base_config.cp(f'{dir}/base.config')
    res.append(f'{dir}/base.config')

    # Test Base Config in QEMU
    booter = KernelBooter()
    bz_image = builder.build_kernel()

    booted = booter.boot(img_path, bz_image, f'{dir}/base_qemu.log')
    if not booted:
        print('Base config failed to boot in QEMU. Aborting sample generation.')
    else:
        print('Base config booted successfully in QEMU.')

    res.append(booted)
    res.append(f'{dir}/base_qemu.log')

    # Get KLocalizer Config
    repo.clean()
    repo.checkout(end)

    klocalizer = KLocalizer()

    klocalizer_config = klocalizer.repair(f'{dir}/changes.patch')
    if klocalizer_config is None:
        print('KLocalizer repair failed. Aborting sample generation.')
        return res
    
    klocalizer_config.cp(f'{dir}/klocalizer.config')
    os.remove(f'{dir}/changes.patch.kloc_targets')

    res.append(f'{dir}/klocalizer.config')

    # Test KLocalizer Config in QEMU
    klocalizer_config.cp(f'{kernel_src}/.config')
    bz_image = builder.build_kernel()
    booted = booter.boot(img_path, bz_image, f'{dir}/klocalizer_qemu.log')

    if not booted:
        print('KLocalizer config failed to boot in QEMU.')
    else:
        print('KLocalizer config booted successfully in QEMU.')

    res.append(booted)
    res.append(f'{dir}/klocalizer_qemu.log')

    return res
