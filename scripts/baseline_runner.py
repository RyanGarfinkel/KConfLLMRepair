import sys
sys.path.insert(0, '/workspace')

from src.tools.syzkaller import Syzkaller
from src.tools.klocalizer import KLocalizer
from src.utils.log import log_info, log_success, log_error
from src.kernel.builder import Builder
from src.kernel.repository import KernelRepo
from src.tools.klocalizer import KLocalizer
from src.kernel.boot import KernelBooter
from src.config import kernel_src
import datetime
import os

output_dir = f'/workspace/data/baseline/{datetime.datetime.now().strftime("%Y%m%d")}'

syzkaller = Syzkaller()
builder = Builder()
repo = KernelRepo()
klocalizer = KLocalizer()
booter = KernelBooter()

num_configs = 1

log_info(f'Starting baseline configuration generation for {num_configs} configurations...')

data = []

for i in range(num_configs):

    log_info(f'Generating sample {i + 1}/{num_configs}...')

    sample_dir = f'{output_dir}/sample_{i}'
    os.makedirs(sample_dir, exist_ok=True)

    # Generate patch
    start, end = builder.build_patch(f'{sample_dir}/changes.patch')
    repo.checkout(end)

    # Generate syzkaller configuration
    wasBuilt = syzkaller.build_for(end)
    if not wasBuilt:
        log_error('Syzkaller build failed. Aborting sample generation.')
        continue

    base_config = syzkaller.generate_base_config(f'{sample_dir}/base.config')
    if base_config is None:
        log_error('Failed to generate base syzkaller config. Aborting sample generation.')
        continue

    base_config.cp(f'{kernel_src}/.config')
    base_config.cp(f'{sample_dir}/base.config')

    # Run Klocalizer
    repo.clean()
    repo.checkout(end)
    klocalizer_config = klocalizer.repair(f'{sample_dir}/changes.patch')
    klocalizer_config.cp(f'{sample_dir}/klocalizer.config')

    # Build and test
    klocalizer_config.cp(f'{kernel_src}/.config')

    bz_image = builder.build_kernel()
    does_boot = booter.boot(bz_image, f'{sample_dir}/boot.log')

    log_info(f'Sample {i + 1} boot result: {"SUCCESS" if does_boot else "FAILURE"}')
