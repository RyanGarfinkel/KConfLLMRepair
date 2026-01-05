# from time import time
# from src.utils.kconfig import apply_llm_suggestions, calculate_delta, chunk_delta
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from src.llm.client import get_suggestions
# import json
import os

from src.kernel.repository import KernelRepo
from src.tools.syzkaller import Syzkaller
from src.tools.klocalizer import KLocalizer
from src.config import kernel_src
from src.kernel.builder import Builder
from src.kernel.repository import KernelRepo
from src.kernel.boot import KernelBooter
from src.utils.log import log_info, log_success, log_error

# def aggregate_suggestions(delta_chunks):

#     print('Obtaining LLM suggestions for all delta chunks...')

#     with ThreadPoolExecutor(max_workers=1) as executor:
#         futures = {executor.submit(get_suggestions, delta): delta for delta in delta_chunks.values()}

#         aggregated_suggestions = {}

#         for future in as_completed(futures):
#             try:
#                 suggestions = future.result()
#                 aggregated_suggestions.update(suggestions)
#             except Exception as e:
#                 print(f'Error obtaining suggestions for chunk: {e}')

#     print(f'Aggregated suggestions for {len(aggregated_suggestions)} options from LLM.')

#     return aggregated_suggestions


# def iteration(commit=kernel_repo.head.commit):

#     os.chdir(kernel_src)

#     patch_path, parent_commit = fetch_patch(commit)
#     if patch_path is None:
#         print('No patch to process. Exiting iteration.')
#         return
    
#     base_config = make_defconfig(commit.hexsha)

#     # QEMU TEST base config

    
#     klocalizer_config = klocalizer_repair(commit.hexsha, patch_path)

#     # DO QEMU TEST HERE ON KLOCALIZER CONFIG

#     base_config = '/workspace/data/base_configs/9448598b22c50c8a5bb77a9103e2d49f134c9578.config'
#     klocalizer_config = '/workspace/data/klocalizer_configs/9448598b22c50c8a5bb77a9103e2d49f134c9578.config'

#     delta, _ = calculate_delta(base_config, klocalizer_config)
#     delta_chunks = chunk_delta(delta)

#     llm_suggestions = aggregate_suggestions(delta_chunks)

#     llm_config = apply_llm_suggestions(commit.hexsha, klocalizer_config, llm_suggestions)

#     # Test LLM Suggestions

#     os.chdir('/workspace')

#     return None

def generate_single_baseline(dir):

    res = []

    builder = Builder()
    repo = KernelRepo()

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
    
    print('here 1:', base_config.path)
    base_config.cp(f'{kernel_src}/.config')
    print('here 2:', base_config.path)
    builder.merge_with_kvm_config(base_config.path)
    base_config.refresh()

    base_config.cp(f'{dir}/base.config')
    res.append(f'{dir}/base.config')

    # Test Base Config in QEMU
    booter = KernelBooter()
    bz_image = builder.build_kernel()

    booted = booter.boot(bz_image, f'{dir}/base_qemu.log')
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
    booted = booter.boot(bz_image, f'{dir}/klocalizer_qemu.log')

    if not booted:
        print('KLocalizer config failed to boot in QEMU.')
    else:
        print('KLocalizer config booted successfully in QEMU.')

    res.append(booted)
    res.append(f'{dir}/klocalizer_qemu.log')

    return res