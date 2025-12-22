
from git import Repo
import subprocess
import os

kernel_src = '/workspace/kernel'
if not os.path.exists(kernel_src):
    print('Kernel source path does not exist.')
    exit(1)

kernel_repo = Repo(kernel_src)

code_change_dir = '/workspace/data/code_changes'
os.makedirs(code_change_dir, exist_ok=True)

commit_window = 25

def checkout(commit):
    print(f'Checking out commit {commit}...')
    kernel_repo.git.reset('--hard')
    kernel_repo.git.checkout(commit)

def fetch_kernel_code_changes(commit):

    print(f'Fetching code changes for commit {commit.hexsha}...')

    start_commit = commit
    num_commits = 0
    for _ in range(commit_window):
        if not start_commit.parents:
            print('Reached the initial commit of the repository.')
            break

        start_commit = start_commit.parents[0]
        num_commits += 1
    
    diff = kernel_repo.git.diff(start_commit.hexsha, commit.hexsha, '--no-merges')
    
    if diff:
        print('diff fetched successfully.')
    else:
        print('No changes found between the specified commits.')

    output_file = f'{code_change_dir}/{commit.hexsha}.patch'

    with open(output_file, 'w') as f:
        f.write(diff)
    
    print(f'Diff written to {output_file}')

    return start_commit, commit, num_commits, output_file

def build_kernel(commit, config_path):

    print(f'Checking out commit {commit}...')
    kernel_repo.git.reset('--hard')
    kernel_repo.git.checkout(commit)

    result = subprocess.run(['cp', config_path, f'{kernel_src}/.config'], check=True)
    if result.returncode != 0:
        raise Exception('Failed to copy config file.')

    print('Building the kernel...')

    os.chdir(kernel_src)

    result = subprocess.run(['make', 'ARCH=x86', 'CROSS_COMPILE=x86_64-linux-gnu-', '-j$(nproc)'], check=True)

    if result.returncode != 0:
        raise Exception('Kernel build failed.')
    
    os.chdir('/workspace')
    
    print('Kernel built successfully.')

    return f'{kernel_src}/arch/x86/boot/bzImage'

