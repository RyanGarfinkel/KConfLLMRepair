
from kernel import kernel_src, checkout, fetch_kernel_code_changes, kernel_repo
import subprocess
import click
import os

superc_linux_script_path = '/usr/local/bin/superc-linux'

base_config_dir = '/workspace/data/base_configs'
os.makedirs(base_config_dir, exist_ok=True)

klocalizer_config_dir = '/workspace/data/klocalizer_configs'
os.makedirs(klocalizer_config_dir, exist_ok=True)

def make_defconfig(commit_hash):

    print('Making defconfig for x86_64 architecture...')

    result = subprocess.run(['make', 'ARCH=x86', 'CROSS_COMPILE=x86_64-linux-gnu-', 'olddefconfig'], cwd=kernel_src)
    if result.returncode != 0:
        raise Exception('Failed to make olddefconfig')
    
    config_path = f'{base_config_dir}/{commit_hash}.config'

    result = subprocess.run(['cp', f'{kernel_src}/.config', config_path], check=True)
    if result.returncode != 0:
        raise Exception('Failed to copy base config file')
    
    print('Defconfig created and copied.')

    return config_path

def klocalizer_repair(commit_hash, patch_path):

    print('Running KLocalizer repair...')

    cmd = f'klocalizer \
        --superc-linux-script {superc_linux_script_path} \
        --include-mutex {patch_path} \
        --cross-compiler gcc \
        --arch x86_64'

    result = subprocess.run([cmd], shell=True, check=True, cwd=kernel_src)
    if result.returncode != 0:
        raise Exception(f'KLocalizer repair failed: {result.stderr}')
    
    config_path = f'{klocalizer_config_dir}/{commit_hash}.config'

    result = subprocess.run(['cp', f'{kernel_src}/0-x86_64.config', config_path], check=True)
    if result.returncode != 0:
        raise Exception('Failed to copy KLocalizer config file')
        
    print('KLocalizer repair completed.')

    return config_path

def fetch_base_klocalizer_configs(commit):

    _, _, _, patch_path = fetch_kernel_code_changes(commit)

    base_config_path = make_defconfig(commit.hexsha)
    klocalizer_config_path = klocalizer_repair(commit.hexsha, patch_path)


    return base_config_path, klocalizer_config_path

@click.command()
@click.option('--commit', required=False, default=kernel_repo.head.commit.hexsha, help='The commit to repair')
def main(commit):
    commit_obj = kernel_repo.commit(commit)
    base_config_path, klocalizer_config_path = fetch_base_klocalizer_configs(commit_obj)

    print(f'Base config path: {base_config_path}')
    print(f'KLocalizer config path: {klocalizer_config_path}')


if __name__ == '__main__':
    main()