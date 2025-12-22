from git import Repo
import sys
import os

kernel_src = '/workspace/kernel'

if not kernel_src or not os.path.exists(kernel_src):
    print('Error: kernel repo_path is empty or does not exist')
    exit(1)

code_change_dir = '/workspace/data/code_changes'
os.makedirs(code_change_dir, exist_ok=True)

kernel_repo = Repo(kernel_src)

commit_window = 25

def fetch_code_changes(end_commit):

    end_commit = kernel_repo.commit(end_commit)
    start_commit = end_commit
    num_commits = 0
    for _ in range(commit_window):
        if not start_commit.parents:
            print('Reached the initial commit of the repository.')
            break

        start_commit = start_commit.parents[0]
        num_commits += 1

    print(f'Fetching code changes from commit {start_commit.hexsha} to {end_commit.hexsha}...')
    
    diff = kernel_repo.git.diff(start_commit.hexsha, end_commit.hexsha, '--no-merges')
    
    if diff:
        print('diff fetched successfully.')
    else:
        print('No changes found between the specified commits.')

    output_file = f'{code_change_dir}/{end_commit.hexsha}.patch'

    with open(output_file, 'w') as f:
        f.write(diff)
    
    print(f'Diff written to {output_file}')

    return start_commit, end_commit, num_commits, output_file

if __name__ == '__main__':

    latest_commit = kernel_repo.head.commit
    
    start_commit, end_commit, num_commits, output_file = fetch_code_changes(latest_commit)

    print(f'Start Commit: {start_commit.hexsha}')
    print(f'End Commit: {end_commit.hexsha}')
    print(f'Number of commits between: {num_commits}')
    print(f'Code changes saved to: {output_file}')
