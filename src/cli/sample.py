from src.utils import log, dispatcher
from src.config import settings
from src.kernel import worktree
from src.utils import file_lock
from src.models import Sample
from typing import Callable
from src.core import Kernel
import shutil
import click
import json
import os

main_repo = worktree.main_repo

def sample_commits(n: int) -> tuple[dict, list[Sample]]:
    
    kernel = Kernel(settings.kernel.KERNEL_SRC)

    summary = {
        'kernel_version': kernel.version,
        'end_commit': main_repo.head.commit.hexsha,
        'end_commit_date': main_repo.head.commit.committed_datetime.isoformat(),
        'n': n,
    }

    samples = [
        Sample(
            sample_dir=f'{settings.runtime.SAMPLE_DIR}/sample_{i}',
            kernel_src='',
            kernel_version='',
            end_commit=main_repo.head.commit.hexsha,
            end_commit_date=main_repo.head.commit.committed_datetime.isoformat(),
        ) for i in range(n)
    ]

    return summary, samples
 
def make_sample(sample: Sample, kernel: Kernel) -> bool:

    sample_dir = sample.sample_dir

    if os.path.exists(sample_dir):
        shutil.rmtree(sample_dir)

    log.info('Creating new sample...')
    
    os.makedirs(sample_dir, exist_ok=True)

    path = f'{sample_dir}/.config'
    if not kernel.make_rand_config(path):
        return False
    
    sample.config = path
    
    log.success('Sample created successfully.')

    return True

def save_samples(summary: dict, completed_samples: list[Sample]):

    with file_lock:
        with open(f'{settings.runtime.SAMPLE_DIR}/sampling.json', 'w') as f:
            json.dump({
                'summary': summary,
                'samples': [s.model_dump() for s in completed_samples]
            }, f, indent=4)

def generate_samples(n: int, complete_callback: Callable[[int, Sample], None] | None = None) -> tuple[dict, list[Sample]]:

    summary, samples = sample_commits(n)
    save_samples(summary, [])

    completed = []
    def process(i: int):
        sample = samples[i]

        kernel_src = worktree.create(sample.end_commit)
        kernel = Kernel(kernel_src)

        sample = Sample(
            **{**sample.model_dump(), 'kernel_src': kernel_src, 'kernel_version': kernel.version}
        )

        completed.append(sample)
        save_samples(summary, completed)

        try:
            if not make_sample(sample, kernel):
                log.error(f'Failed to create sample {i + 1}.')
                return

            save_samples(summary, completed)

            if complete_callback is not None:
                complete_callback(i, sample)
        finally:
            if settings.runtime.CLEANUP:
                log.info(f'Cleaning up sample {i + 1} worktree...')
                worktree.cleanup(sample.kernel_src)
        
    tasks = [lambda idx=i: process(idx) for i in range(n)]
    dispatcher.run_tasks(tasks, desc='Generating samples')

    return summary, completed

@click.command()
@click.option('-n', default=10, help='Number of samples to generate.')
@click.option('--jobs', '-j', default=8, help='Number of parallel jobs to use for building kernels.')
@click.option('--max-threads', '-t', default=8, help='Maximum number of samples generating at once.')
@click.option('--cleanup', is_flag=True, default=False, help='Clean up kernel worktrees after sampling.')
def main(n: int, jobs: int, max_threads: int, cleanup: bool):

    settings.runtime.MAX_THREADS = max_threads
    settings.runtime.CLEANUP = cleanup
    settings.runtime.JOBS = jobs

    log.info(f'Starting sample generation for {n} samples...')

    generate_samples(n)

    log.info('Sample generation completed.')

if __name__ == '__main__':
    main()