
from src.config import kernel_src, base_config_dir
import subprocess
import os

def make_defconfig(commit_hash):

    print('Making defconfig for x86_64 architecture...')

    result = subprocess.run('make ARCH=x86 CROSS_COMPILE=x86_64-linux-gnu- defconfig', shell=True, cwd=kernel_src)
    if result.returncode != 0:
        raise Exception('Failed to make defconfig')
    
    config_path = f'{kernel_src}/.config'

    result = subprocess.run(f'cp {kernel_src}/.config {base_config_dir}/{commit_hash}.config', shell=True, check=True)
    if result.returncode != 0:
        raise Exception('Failed to copy base config file')

    print('Defconfig created.')

    return config_path

def build_kernel():

    print('Building the kernel...')

    os.chdir(kernel_src)

    result = subprocess.run(f'make ARCH=x86 CROSS_COMPILE=x86_64-linux-gnu- -j$(nproc)', shell=True, check=True)
    if result.returncode != 0:
        raise Exception('Kernel build failed.')
    
    os.chdir('/workspace')

    print('Kernel built successfully.')

    return f'{kernel_src}/arch/x86/boot/bzImage' 
