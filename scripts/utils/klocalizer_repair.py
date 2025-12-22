from fetch_code_changes import kernel_src, kernel_repo, code_change_dir
import subprocess
import click
import os

superc_linux_script_path = '/usr/local/bin/superc-linux'

base_config_dir = '/workspace/data/base_configs'
os.makedirs(base_config_dir, exist_ok=True)

klocalizer_config_dir = '/workspace/data/klocalizer_configs'
os.makedirs(klocalizer_config_dir, exist_ok=True)

def klocalizer_repair(commit):
    
    code_change_file_path = f'{code_change_dir}/{commit}.patch'
    
    commit = commit.split('_')[0]
   
    print('Cleaning any changes in the kernel repository...')
    kernel_repo.git.reset('--hard')
    
    print(f'Checking out commit {commit}...')
    kernel_repo.git.checkout(commit)
    
    os.chdir(kernel_src)

    print('Making defconfig for x86_64 architecture...')
    result = subprocess.run(['make', 'defconfig', 'ARCH=x86_64'], check=True)

    os.chdir('/workspace')

    if result.returncode != 0:
        raise Exception('Failed to make defconfig for x86_64 architecture')
    
    base_config_file_path = os.path.join(base_config_dir, f'{commit}.config')
    result = subprocess.run(['cp', f'{kernel_src}/.config', base_config_file_path], check=True)

    if result.returncode != 0:
        raise Exception('Failed to copy base config file')
    
    print(f'Running KLocalizer repair for commit {commit}...')
    result = subprocess.run([
        'klocalizer',
        '--superc-linux-script', superc_linux_script_path,
        '--include-mutex', code_change_file_path,
        '--cross-compiler', 'gcc',
        '--arch', 'x86_64',
    ], check=True, capture_output=False, text=True, cwd=kernel_src)

    if result.returncode != 0:
        raise Exception(f'KLocalizer repair failed for commit {commit}: {result.stderr}')
    
    print(f'KLocalizer repair completed for commit {commit}.')

    klocalizer_config_file_path = os.path.join(klocalizer_config_dir, f'{commit}.config')
    result = subprocess.run(['cp', f'{kernel_src}/0-x86_64.config', klocalizer_config_file_path], check=True)

    if result.returncode != 0:
        raise Exception('Failed to copy KLocalizer config file')

    return base_config_file_path, klocalizer_config_file_path

@click.command()
@click.option('--commit', required=True, help='The commit to repair')
def main(commit):
    base_path, klocalizer_path = klocalizer_repair(commit=commit)
    print(f'Base config saved to: {base_path}')
    print(f'KLocalizer config saved to: {klocalizer_path}')

if __name__ == '__main__':
    main()