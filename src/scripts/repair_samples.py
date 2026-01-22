from src.kernel import KernelRepo
from src.models import Sample
from src.utils import log
import subprocess
import click

def repair_samples(n: int, model_override: str | None = None, max_iterations: int = 5):

    samples = Sample.get_samples(n)

    for i, sample in enumerate(samples):

        log.info(f'Repairing sample {i + 1}...')

        kernel_src = KernelRepo.create_worktree(sample.commit)
        base = sample.base
        modified = sample.modified
        patch = sample.patch

        cmd = [
            'python3', '-m', 'src.scripts.repair',
            '--base', base,
            '--modified', modified,
            '--patch', patch,
            '--kernel-src', kernel_src,
            '--output', sample.output,
            '--max-iterations', str(max_iterations),
        ]

        if model_override:
            cmd.extend(['--model-override', model_override])

        subprocess.run(cmd, check=True)
    

@click.command()
@click.option('--n', default=10, help='Number of samples to repair.')
@click.option('--model-override', default=None, help='Override the default LLM model to use for repair.')
@click.option('--max-iterations', default=5, type=int, help='Override the maximum number of iterations for the agent.')
def main(n: int, model_override: str | None = None, max_iterations: int = 5):

    log.info(f'Starting repair process for {n} samples...')

    if model_override:
        log.info(f'Using model override: {model_override}')
    else:
        log.info('Using default model based on available API keys.')

    repair_samples(n, model_override, max_iterations)

    log.info('Repair process completed.')

if __name__ == '__main__':
    main()