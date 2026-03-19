from src.config import settings, log_settings
from src.experiment import sampler
from src.utils import log
import click

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
def main(n: int, mode: str, since: str, jobs: int, max_threads: int, cleanup: bool, commit_window: int, arch: str):

	settings.runtime.OUTPUT_DIR = f'{settings.runtime.OUTPUT_DIR}/{arch}'
	settings.runtime.MAX_THREADS = max_threads
	settings.runtime.CLEANUP = cleanup
	settings.runtime.JOBS = jobs
	settings.runtime.COMMIT_WINDOW = commit_window
	settings.kernel.ARCH = arch

	log_settings()
	log.info(f'Starting {mode} sample generation for {n} samples...')

	if mode == 'patch':
		sampler.patch(n, since)
	else:
		sampler.random(n)

	log.info('Sample generation completed.')

if __name__ == '__main__':
	main()
