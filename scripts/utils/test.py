from klocalizer_repair import klocalizer_repair
from fetch_code_changes import fetch_code_changes, kernel_repo

end_commit = kernel_repo.head.commit

start_commit, end_commit, num_commits, output_file = fetch_code_changes(end_commit)

base_path, klocalizer_path = klocalizer_repair(commit=end_commit.hexsha)

print(f'Base config saved to: {base_path}')
print(f'KLocalizer config saved to: {klocalizer_path}')