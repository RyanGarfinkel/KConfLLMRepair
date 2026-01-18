from src.utils import log, dispatcher
from src.kernel import KernelRepo
from src.models import SampleRaw
from src.config import settings
from src.tools import syzkaller
from src.core import Kernel
from random import randint
from git import Repo
import click
import os

def select_commits(repo: Repo, n: int) -> tuple[int, int, list[tuple[str, str]]]:

    log.info(f'Performing systematic random sampling of {n} commits from the repository...')

    all_commits = repo.git.rev_list('HEAD', '--since=2020-01-01').splitlines()
    total_commits = len(all_commits) - settings.runtime.COMMIT_WINDOW
    k = total_commits // n

    start = randint(0, k)

    # Selecting commits
    commits = [SampleRaw(
        end_commit=all_commits[start + i * k],
        start_commit=all_commits[start + i * k + settings.runtime.COMMIT_WINDOW],
        commit_date=repo.commit(all_commits[start + i * k]).committed_datetime.isoformat(),
        commit_window=settings.runtime.COMMIT_WINDOW,
        dir=f'{settings.runtime.SAMPLE_DIR}/sample_{i}'
    ) for i in range(n)]

    log.info(f'Selected {n} commits, k is {k}, starting with commit {commits[0].start_commit}.')

    sampling_params = {
        'start': start,
        'k': k,
        'total_commits': len(all_commits),
        'latest_commit': repo.commit(all_commits[0]).authored_datetime.isoformat(),
        'earliest_commit': repo.commit(all_commits[-1]).authored_datetime.isoformat(),
    }

    del all_commits

    return sampling_params, commits

def make_sample(sample: SampleRaw):

    os.makedirs(sample.dir, exist_ok=True)
    
    kernel_src = KernelRepo.create_worktree(sample.end_commit)
    kernel = Kernel(kernel_src)

    log.info('Running syzkaller to generate base configuration...')

    if not syzkaller.run(kernel_src, f'{sample.dir}/base.config'):
        log.error('Failed to run syzkaller for sample generation.')
        kernel.cleanup()
        return

    # Verifies base is valid
    
    log.info('Verifying base configuration is valid...')

    if not kernel.build(f'{sample.dir}/base.config', f'{sample.dir}/build.log'):
        log.error('Failed to build kernel with base configuration.')
        kernel.cleanup()
        return

    kernel.load_config(f'{sample.dir}/base.config')
    
    if not kernel.boot(f'{sample.dir}/boot.log'):
        log.error('Failed to boot kernel with base configuration.')
        kernel.cleanup()
        return
    
    log.success('Base configuration is valid and bootable.')
    sample.isBaseBootable = True

    log.info('Generating sample patch...')
    kernel.create_patch(sample.dir)

    log.info('Running KLocalizer...')
    kernel.run_klocalizer(sample.dir)

    kernel.cleanup()

def make_samples(n: int):

    repo = Repo(settings.kernel.KERNEL_SRC)
    sampling_params, commits = select_commits(repo, n)

    for i, sample in enumerate(commits):
        log.info(f'Generating sample {i + 1}/{n}...')
        make_sample(sample)
        SampleRaw.save_all(sampling_params, commits[:i + 1], f'{settings.runtime.SAMPLE_DIR}/info.json')

@click.command()
@click.option('--n', default=10, help='Number of samples to generate.')
@click.option('--commit-window', default=250, help='Number of commits to include in each patch.')
@click.option('--max-threads', default=1, help='Maximum number of threads to use for sample generation.')
@click.option('--jobs', default=8, help='Number of parallel cores to use per sample generation.')
def main(n: int, commit_window: int, max_threads: int, jobs: int):

    log.info('Starting sample generation...')
    log.info(f'Using {max_threads} threads for sample generation.')
    log.info(f'Using {jobs} parallel cores per sample generation.')

    settings.runtime.COMMIT_WINDOW = commit_window
    settings.runtime.MAX_THREADS = max_threads
    settings.runtime.JOBS = jobs

    make_samples(n)

    log.info('Sample generation completed.')
if __name__ == '__main__':
    main()
