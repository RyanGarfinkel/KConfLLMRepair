from src.config import settings
from src.models import Sample
from src.core import Kernel
from src.utils import log
from git import Repo
import shutil
import click
import os

def make_sample(i: int, commit: str) -> Sample | None:

    log.info(f'Generating sample {i + 1}...')
    
    global active_kernel

    sample_dir = f'{settings.SAMPLE_DIR}/sample_{i}'
    os.makedirs(sample_dir, exist_ok=True)

    active_kernel = kernel = Kernel(commit)

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
        num_commits=settings.COMMIT_WINDOW,
        patch=f'{sample_dir}/changes.patch'
    )

    # Stage 2: KLocalizer
    sample.klocalizer_log = f'{sample_dir}/klocalizer.log'
    if not kernel.run_klocalizer(sample_dir):
        kernel.cleanup()
        return sample

    sample.config = f'{sample_dir}/klocalizer.config'
    shutil.copy(f'{kernel.repo.path}/.config', sample.config)
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

def make_all_samples(n: int) -> list[Sample]:

    repo = Repo(settings.KERNEL_SRC)
    commit = repo.head.commit.hexsha

    samples = []
    for i in range(n):
        sample = make_sample(i, commit)
        if sample is not None:
            samples.append(sample)
            commit = sample.start_commit

            Sample.save_samples(samples)
    
@click.command()
@click.option('--n', default=10, help='Number of samples to generate.')
@click.option('--commit-window', default=250, help='Number of commits to include in each patch.')
def main(n: int, commit_window: int):

    log.info('Starting sample generation...')
    log.info(f'Generating {n} samples, commit window is {commit_window}.')

    settings.COMMIT_WINDOW = commit_window

    make_all_samples(n)

    log.info('Sample generation completed.')

if __name__ == '__main__':
    main()
    