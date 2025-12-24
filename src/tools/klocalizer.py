from src.config import kernel_src, klocalizer_config_dir, superc_linux_script_path
import subprocess

def repair(commit_hash, patch_path):
    
    config_path = f'{klocalizer_config_dir}/{commit_hash}.config'

    print('Running klocalizer repair...')

    cmd = f'klocalizer \
        --superc-linux-script {superc_linux_script_path} \
        --include-mutex {patch_path} \
        --cross-compiler gcc \
        --arch x86_64'
    
    result = subprocess.run(cmd, shell=True, check=True, cwd=kernel_src)
    if result.returncode != 0:
        raise Exception(f'klocalizer repair failed: {result.stderr}')

    result = subprocess.run(['cp', f'{kernel_src}/0-x86_64.config', config_path], check=True)
    if result.returncode != 0:
        raise Exception('Failed to copy klocalizer config file')
    
    print('klocalizer repair completed.')

    return config_path
