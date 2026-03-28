from src.config import settings, log_settings
from src.experiment import sampler
from src.utils import log
import click
import os

def parse_constraints(path: str) -> tuple[set[str], set[str]]:
	if not os.path.exists(path):
		raise click.UsageError(f'Constraints file not found: {path}')

	hard_define: set[str] = set()
	hard_undefine: set[str] = set()

	with open(os.path.abspath(path)) as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			if line.startswith('!'):
				hard_undefine.add(line[1:])
			else:
				hard_define.add(line)

	return hard_define, hard_undefine

@click.command()
@click.option('-n', default=10, help='Number of samples to generate.')
@click.option('--patch', 'mode', flag_value='patch', help='Generate patch-based samples.')
@click.option('--random', 'mode', flag_value='random', default=True, help='Generate random config samples (default).')
@click.option('--since', default='2020-01-01', help='Only consider commits after this date (used with --patch).')
@click.option('--jobs', '-j', default=8, help='Number of parallel jobs to use for building kernels.')
@click.option('--max-threads', '-t', default=1, help='Maximum number of samples generating at once.')
@click.option('--cleanup', is_flag=True, default=False, help='Clean up kernel worktrees after sampling.')
@click.option('--commit-window', default=500, help='Number of commits between start and end commit for patch samples.')
@click.option('--arch', '-a', default='x86_64', help='Target architecture (x86_64 or arm64).')
@click.option('--constraints', default=None, help='Path to a hard constraints file (OPTION to define, !OPTION to undefine).')
def main(n: int, mode: str, since: str, jobs: int, max_threads: int, cleanup: bool, commit_window: int, arch: str, constraints: str | None):

	settings.runtime.OUTPUT_DIR = f'{settings.runtime.OUTPUT_DIR}/{arch}'
	settings.runtime.MAX_THREADS = max_threads
	settings.runtime.CLEANUP = cleanup
	settings.runtime.JOBS = jobs
	settings.runtime.COMMIT_WINDOW = commit_window
	settings.kernel.ARCH = arch

	settings.kernel.DEBIAN_IMG = os.environ.get('DEBIAN_IMG_ARM64') if arch == 'arm64' else os.environ.get('DEBIAN_IMG_AMD64', settings.kernel.DEBIAN_IMG)

	log_settings()
	log.info(f'Starting {mode} sample generation for {n} samples...')

	hard_define, hard_undefine = parse_constraints(constraints) if constraints else (set(), set())

	if mode == 'patch':
		sampler.patch(n, since, hard_define, hard_undefine)
	else:
		sampler.random(n, hard_define, hard_undefine)

	log.info('Sample generation completed.')

if __name__ == '__main__':
	main()
