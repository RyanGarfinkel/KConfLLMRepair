from .sample import generate_samples
from .repair import repair
from src.models import Sample, State, Input
from src.utils import dispatcher
from src.llm import Session
from src.config import settings
from src.utils import log
import click
import json

def read_samples(n: int) -> list[Sample]:
    with open(f'{settings.runtime.SAMPLE_DIR}/sampling.json', 'r') as f:
        data = json.load(f)
        samples = [Sample(**s) for s in data.get('samples', [])]
    
    return samples[:n]

def repair_all(samples: list[Sample]):

    log.info('Starting repair of all samples...')

    tasks = [lambda i=i, s=sample: repair_sample(i, s) for i, sample in enumerate(samples)]
    dispatcher.run_tasks(tasks, desc='Repairing samples')

def repair_sample(i: int, sample: Sample):

    log.info(f'Starting repair for sample {i + 1}...')

    input = Input(
        sample.base_config,
        sample.modified_config,
        sample.patch,
        output_dir=sample.sample_dir
    )

    repair(input, sample.kernel_src, complete_callback=repair_callback)

def repair_callback(state: State, session: Session):
    # TODO: Summarize all sample metrics
    pass

def run_experiment(n: int, since: str, skip_generation: bool, skip_repair: bool):

    log.info(f'Starting experiment with {n} samples...')

    if skip_generation and not skip_repair:
        log.info('Reading existing samples from disk...')
        samples = read_samples(n)
        repair_all(samples)
    elif not skip_generation:
        log.info('Generating new samples...')

        callback = None if skip_repair else repair_sample
        generate_samples(n, since, callback)
    else:
        log.info('Skipping both sample generation and repair phases.')

@click.command()
@click.option('-n', default=10, help='Number of samples to generate.')
@click.option('--since', default='2020-01-01', help='Approximates the start commit date for sampling.')
@click.option('--commit-window', '-w', default=25, help='Number of commits in each patch window.')
@click.option('--jobs', '-j', default=8, help='Number of parallel jobs to use for building kernels.')
@click.option('--model', '-m', default='gemini-3-pro-preview', help='Override the default LLM model to use for repair.')
@click.option('--max-threads', '-t', default=8, help='Maximum number of samples generating at once.')
@click.option('--skip-generation', is_flag=True, help='Skip the sample generation phase and only perform repair on existing samples.')
@click.option('--skip-repair', is_flag=True, help='Skip the sample generation phase and only perform repair on existing samples.')
@click.option('--cleanup', is_flag=True, help='Clean up kernel worktrees after processing samples.')
def main(n: int, since: str, commit_window: int, model: str, jobs: int, max_threads: int, skip_generation: bool, skip_repair: bool, cleanup: bool):

    settings.runtime.COMMIT_WINDOW = commit_window
    settings.runtime.MAX_THREADS = max_threads
    settings.agent.MODEL = model
    settings.runtime.JOBS = jobs
    settings.runtime.CLEANUP = cleanup

    run_experiment(n, since, skip_generation, skip_repair)

if __name__ == '__main__':
    main()
