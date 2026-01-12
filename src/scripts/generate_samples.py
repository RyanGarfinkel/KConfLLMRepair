from src.config import settings
from dataclasses import asdict
from src.models import Sample
from src.tools import booter
from src.core import Kernel
from src.utils import log
from git import Repo
import pandas as pd
import signal
import click
import sys
import os

active_kernel = None
def handler(a, b):

    global active_kernel
    
    if active_kernel is not None:
        log.info('Cleaning up active kernel worktree...')
        active_kernel.cleanup()
    
    sys.exit(0)

signal.signal(signal.SIGINT, handler)

def make_sample(i: int, commit: str, commit_window: int) -> Sample | None:

    log.info(f'Generating sample {i}...')
    
    global active_kernel

    sample_dir = f'{settings.SAMPLE_DIR}/sample_{i}'
    os.makedirs(sample_dir, exist_ok=True)

    active_kernel = kernel = Kernel(commit)

    # Stage 1: Patch Creation
    created_patch, start = kernel.create_patch(sample_dir, commit_window)
    if not created_patch:
        kernel.cleanup()
        return None

    sample = Sample(
        id=str(i),
        dir=sample_dir,
        start_commit=start,
        end_commit=commit,
        num_commits=commit_window,
        patch=f'{sample_dir}/changes.patch'
    )

    # Stage 2: KLocalizer
    sample.klocalizer_log = f'{sample_dir}/klocalizer.log'
    if not kernel.run_klocalizer(sample_dir):
        kernel.cleanup()
        return sample

    sample.klocalizer_succeeded = True
    sample.config = f'{sample_dir}/klocalizer.config'

    # Stage 3: Build
    sample.build_log = f'{sample_dir}/build.log'
    if not kernel.build(sample_dir):
        kernel.cleanup()
        return sample

    sample.build_succeeded = True    

    # Stage 4: QEMU Test
    sample.qemu_succeeded = booter.test(kernel, sample_dir)
    sample.qemu_log = f'{sample_dir}/qemu.log'

    # Finish
    kernel.cleanup()

    return sample

def make_all_samples(n: int, commit_window: int) -> list[Sample]:

    csv_path = f'{settings.SAMPLE_DIR}/summary.csv'

    repo = Repo(settings.KERNEL_SRC)
    commit = repo.head.commit.hexsha

    samples = []
    for i in range(n):
        sample = make_sample(i, commit, commit_window)
        if sample is not None:
            samples.append(sample)
            commit = sample.start_commit

            df = pd.DataFrame([asdict(s) for s in samples])
            df.to_csv(csv_path, index=False)
    
@click.command()
@click.option('--n', default=10, help='Number of samples to generate.')
@click.option('--commit-window', default=250, help='Number of commits to include in each patch.')
def main(n: int, commit_window: int):

    print(f'Generating {n} samples with a commit window of {commit_window}...')

    make_all_samples(n, commit_window)

    print('Sample generation complete.')

if __name__ == '__main__':
    main()
    