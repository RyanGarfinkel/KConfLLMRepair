from src.utils import log, dispatcher
from src.config import settings
from src.models import Sample
from src.core import Kernel
import click
import os

def make_sample(i: int, commit: str) -> Sample | None:

    log.info(f'Generating sample {i + 1}...')

    sample_dir = f'{settings.runtime.SAMPLE_DIR}/sample_{i}'
    os.makedirs(sample_dir, exist_ok=True)

    kernel = Kernel(commit)

    # Stage 1: Patch Creation
    created_patch, start = kernel.create_patch(sample_dir)
    if not created_patch:
        kernel.cleanup()
        return None

    sample = Sample(
        id=str(i),
        dir=sample_dir,
        start_commit=start,
        end_commit=commit,
        num_commits=settings.runtime.COMMIT_WINDOW,
        patch=f'{sample_dir}/changes.patch'
    )

    # Stage 2: KLocalizer
    sample.klocalizer_log = f'{sample_dir}/klocalizer.log'
    if not kernel.run_klocalizer(sample_dir):
        kernel.cleanup()
        return sample

    sample.config = f'{sample_dir}/klocalizer.config'
    sample.klocalizer_succeeded = True

    # Stage 3: Build
    sample.build_log = f'{sample_dir}/build.log'
    if not kernel.build(sample.config, sample.build_log):
        kernel.cleanup()
        return sample

    sample.build_succeeded = True    

    # Stage 4: QEMU Test
    sample.qemu_log = f'{sample_dir}/qemu.log'
    sample.qemu_succeeded = kernel.boot(sample.qemu_log)

    # Finish
    kernel.cleanup()

    return sample

def make_all_samples(n: int, start_commit: str | None = None) -> list[Sample]:

    ends = Kernel.get_sample_ends(n, start_commit)

    tasks = []
    for i, commit in enumerate(ends):
        # Use lambda with default arguments to capture current values
        tasks.append(lambda idx=i, cmt=commit: make_sample(idx, cmt))

    samples = []    
    def handle_as_completed(sample: Sample | None):
        if sample is not None:
            samples.append(sample)
            Sample.save_samples(samples)

    dispatcher.run_tasks(tasks, handle_as_completed)


    # Sequential
    # samples = []
    # for i in range(n):
    #     sample = make_sample(i, commit)
    #     if sample is not None:
    #         samples.append(sample)
    #         commit = sample.start_commit

    #         Sample.save_samples(samples)




@click.command()
@click.option('--n', default=10, help='Number of samples to generate.')
@click.option('--commit-window', default=250, help='Number of commits to include in each patch.')
@click.option('--jobs', default=8, help='Number of parallel cores to use per sample generation.')
@click.option('--max-threads', default=1, help='Maximum number of threads to use for sample generation.')
@click.option('--start-commit', default=None, help='Starting commit hash for sample generation. If not provided, uses the latest commit.')
def main(n: int, commit_window: int, max_threads: int, start_commit: str | None, jobs: int):

    log.info('Starting sample generation...')
    log.info(f'Generating {n} samples, commit window is {commit_window}.')
    log.info(f'Using {max_threads} threads for sample generation.')
    log.info(f'Using {jobs} parallel cores per sample generation.')

    settings.runtime.COMMIT_WINDOW = commit_window
    settings.runtime.MAX_THREADS = max_threads
    settings.runtime.JOBS = jobs

    make_all_samples(n, start_commit)

    log.info('Sample generation completed.')

if __name__ == '__main__':
    main()
    