from src.config import kernel_repo, patches_dir
import os

window = 25

def fetch_patch(end_commit):

    start_commit = end_commit
    count = 0

    for _ in range(window):
        if not start_commit.parents:
            print('Reached the initial commit of the repository.')
            break

        start_commit = start_commit.parents[0]
        count += 1
    
    print(f'Generating patch between {start_commit.hexsha} and {end_commit.hexsha}...')

    diff = kernel_repo.git.diff(start_commit.hexsha, end_commit.hexsha, '--no-merges')

    if not diff:
        print('No changes found between the specified commits.')
        return None
    
    patch_path = f'{patches_dir}/{end_commit.hexsha}.patch'
    with open(patch_path, 'w') as f:
        f.write(diff)

    print(f'Patch written to {patch_path}')

    return patch_path, start_commit.parents[0] if start_commit.parents else None
