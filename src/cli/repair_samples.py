from src.kernel import KernelRepo
from src.models import Sample
from src.utils import log
import subprocess
import click

def repair_samples(n: int, model: str | None = None, max_iterations: int = 5, jobs: int | None = None):

    samples = Sample.get_samples(n)

    for i, sample in enumerate(samples):

        log.info(f'Repairing sample {i + 1}...')

        kernel_src = f'workspace/worktrees/{sample.end_commit[:12]}' # KernelRepo.create_worktree(sample.end_commit)

        base = sample.base
        modified = sample.modified
        patch = sample.patch

        cmd = [
            'python3', '-m', 'src.cli.repair',
            '--base', base,
            '--modified', modified,
            '--patch', patch,
            '--kernel-src', kernel_src,
            '--output', sample.output,
            '--max-iterations', str(max_iterations),
        ]

        if model:
            cmd.extend(['--model', model])

        if jobs:
            cmd.extend(['--jobs', str(jobs)])

        subprocess.run(cmd, check=True)
    

@click.command()
@click.option('--n', default=10, help='Number of samples to repair.')
@click.option('--model', default=None, help='Override the default LLM model to use for repair.')
@click.option('--max-iterations', default=5, type=int, help='Override the maximum number of iterations for the agent.')
@click.option('--jobs', default=None, type=int, help='Number of jobs to run when building the kernel, otherwise set to 8.')
def main(n: int, model: str | None = None, max_iterations: int = 5, jobs: int | None = None):

    log.info(f'Starting repair process for {n} samples...')

    if model:
        log.info(f'Using model override: {model}')
    else:
        log.info('Using default model based on available API keys.')

    repair_samples(n, model, max_iterations, jobs)

    log.info('Repair process completed.')

if __name__ == '__main__':
    main()