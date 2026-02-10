from src.utils import log, dispatcher
from src.config import settings
from src.kernel import KernelRepo
from src.tools import syzkaller
from src.utils import file_lock
from src.models import Sample
from typing import Callable
from src.core import Kernel
from random import randint
import shutil
import click
import json
import os

main_repo = KernelRepo.main_repo

def sample_commits(n: int, since: str) -> tuple[dict, list[Sample]]:
    
    all_commits = main_repo.git.rev_list('HEAD', f'--since={since}', '--no-merges').splitlines()
    total_commits = len(all_commits) - settings.runtime.COMMIT_WINDOW
    k = total_commits // n

    start = randint(0, k)

    sampling_params = {
        'total_commits': len(all_commits),
        'earliest_commit': main_repo.commit(all_commits[-1]).authored_datetime.isoformat(),
        'latest_commit': main_repo.commit(all_commits[0]).authored_datetime.isoformat(),
        'commit_window': settings.runtime.COMMIT_WINDOW,
        'k': k,
        'n': n,
        'start': start,
    }

    commits = [
        Sample(
            sample_dir=settings.runtime.SAMPLE_DIR + f'/sample_{i}',
            start_commit=all_commits[start + i * k + settings.runtime.COMMIT_WINDOW],
            start_commit_date=main_repo.commit(all_commits[start + i * k + settings.runtime.COMMIT_WINDOW]).committed_datetime.isoformat(),
            end_commit=all_commits[start + i * k],   
            end_commit_date=main_repo.commit(all_commits[start + i * k]).committed_datetime.isoformat(),
            kernel_src='',
            kernel_version='',
            base_builds=False,
            base_boots=False,
        ) for i in range(n)
    ]

    del all_commits

    return sampling_params, commits

def initalize_rand_samples(n: int) -> list[Sample]:

    samples = []

    for i in range(n):
        sample = Sample(
            sample_dir=settings.runtime.SAMPLE_DIR + f'/sample_{i}',
            kernel_src='',
            kernel_version='',
            start_commit=None,
            start_commit_date=None,
            end_commit=main_repo.head.commit.hexsha,
            end_commit_date=main_repo.head.commit.committed_datetime.isoformat(),
            base_builds=False,
            base_boots=False,
        )
        samples.append(sample)

    return samples

def make_syzkaller_base(sample: Sample, kernel: Kernel) -> bool:

    sample_dir = sample.sample_dir

    # Generation
    log.info('Running syzkaller to generate base configuration...')

    if not syzkaller.run(kernel.src, f'{sample_dir}/base.config'):
        log.error('Syzkaller failed to generate a base configuration.')
        return False
    
    sample.base_config = f'{sample_dir}/base.config'
    log.success('Syzkaller successfully generated a base configuration.')

    # Verification
    log.info('Verifying base configuration by building and booting the kernel...')

    if not kernel.load_config(f'{sample_dir}/base.config'):
        log.error('Base configuration failed to load into kernel source.')
        return False
    
    if not kernel.build(f'{sample_dir}/build.log'):
        log.error('Base configuration build failed.')
        return False
    else:
        sample.base_builds = True
    
    if not kernel.boot(f'{sample_dir}/boot.log'):
        log.error('Base configuration boot failed.')
        return False
    
    sample.base_boots = True

    return True

def make_random_base(sample: Sample, kernel: Kernel) -> bool:

    sample_dir = sample.sample_dir

    # Generation
    log.info('Running randconfig to generate base configuration...')

    path = f'{sample_dir}/base.config'
    if not kernel.make_rand_config(path):
        log.error('Randconfig failed to generate a base configuration.')
        return False
    
    sample.base_config = path
    sample.modified_config = path

    log.success('Randconfig successfully generated a base configuration.')

    return True
    
def make_modified(sample: Sample, kernel: Kernel) -> bool:

    sample_dir = sample.sample_dir
    
    # Patch
    log.info('Generating patch for the sample...')
    
    patch_path = f'{sample_dir}/changes.patch'
    if not kernel.make_patch(patch_path):
        click.echo('Failed to generate patch for the sample.')
        return False
    else:
        sample.patch = patch_path
        log.success('Patch generated successfully for the sample.')

    # KLocalizer
    log.info('Running KLocalizer to create modified configuration...')

    if not kernel.load_config(sample.base_config):
        log.error('Base configuration failed to load into kernel source.')
        return False
    
    if not kernel.run_klocalizer(sample.patch, f'{sample_dir}/klocalizer.log'):
        return False
    
    modified_config = f'{sample_dir}/modified.config'
    shutil.copyfile(f'{kernel.src}/.config', modified_config)
    sample.modified_config = modified_config

    log.success('Modified configuration created successfully.')

    return True

def make_sample(sample: Sample, kernel: Kernel, random: bool) -> bool:

    sample_dir = sample.sample_dir

    if os.path.exists(sample_dir):
        shutil.rmtree(sample_dir)

    os.makedirs(sample_dir, exist_ok=True)

    if random:
        if not make_random_base(sample, kernel):
            return False
    else:
        if not make_syzkaller_base(sample, kernel) or not make_modified(sample, kernel):
            return False
    
    log.success('Sample created successfully.')

    return True

def save_samples(params: dict, completed_samples: list[Sample], random: bool):

    if random:
        with open(f'{settings.runtime.SAMPLE_DIR}/sampling.json', 'w') as f:
            json.dump({
                'summary': {
                    'kernel_version': completed_samples[0].kernel_version if completed_samples else None,
                    'end_commit': completed_samples[0].end_commit if completed_samples else None,
                    'end_commit_date': completed_samples[0].end_commit_date if completed_samples else None,
                    'n': params.get('n', 0),
                },
                'samples': [
                    {
                        'dir': s.sample_dir,
                        'config': s.base_config,

                    } for s in completed_samples
                ]
            }, f, indent=4)
    else:
        with open(f'{settings.runtime.SAMPLE_DIR}/sampling.json', 'w') as f:
            json.dump({
                'sampling_params': params,
                'samples': [s.model_dump() for s in completed_samples]
            }, f, indent=4)

def generate_samples(n: int, since: str, random: bool, complete_callback: Callable[[int, Sample], None] | None = None) -> tuple[dict, list[Sample]]:

    if random:
        sampling_params = {}
        samples = initalize_rand_samples(n)
        save_samples({'n': n}, [], random)
    else:
        sampling_params, samples = sample_commits(n, since)
        save_samples(sampling_params, [], random)

    completed = []

    def process(i: int):
        sample = samples[i]

        kernel_src = KernelRepo.create_worktree(sample.end_commit)
        kernel = Kernel(kernel_src)

        sample = Sample(
            **{**sample.model_dump(), 'kernel_src': kernel_src, 'kernel_version': kernel.version}
        )

        with file_lock:
            completed.append(sample)
            save_samples(sampling_params, completed, random)

        if not make_sample(sample, kernel, random):
            log.error(f'Failed to create sample {i + 1}.')
            return
        
        with file_lock:
            save_samples(sampling_params, completed, random)
            
        if complete_callback is not None:
            complete_callback(i, sample)
        
    tasks = [lambda idx=i: process(idx) for i in range(n)]
    dispatcher.run_tasks(tasks, desc='Generating samples')

    return sampling_params, completed

@click.command()
@click.option('-n', default=10, help='Number of samples to generate.')
@click.option('--since', default='2020-01-01', help='Approximates the start commit date for sampling.')
@click.option('--commit-window', '-w', default=25, help='Number of commits in each patch window.')
@click.option('--jobs', '-j', default=8, help='Number of parallel jobs to use for building kernels.')
@click.option('--max-threads', '-t', default=8, help='Maximum number of samples generating at once.')
@click.option('--random', is_flag=True, default=False, help='Use randconfig instead of syzkaller for base configuration generation.')
@click.option('--cleanup', is_flag=True, default=False, help='Clean up kernel worktrees after sampling.')
def main(n: int, since: str, commit_window: int, jobs: int, max_threads: int, random: bool, cleanup: bool):

    settings.runtime.COMMIT_WINDOW = commit_window
    settings.runtime.MAX_THREADS = max_threads
    settings.runtime.JOBS = jobs

    log.info(f'Starting sample generation for {n} samples...')

    _, samples = generate_samples(n, since)

    log.info('Sample generation completed.')

    if not cleanup:
        return
    
    log.info('Cleaning up kernel worktrees...')

    for sample in samples:
        KernelRepo.cleanup(sample.kernel_src)

if __name__ == '__main__':
    main()