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
import os

load_dotenv()

def generate_single_baseline(dir):

    res = []

    builder = Builder()
    repo = KernelRepo()

    img_path = os.getenv('TRIXIE_IMG')

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
