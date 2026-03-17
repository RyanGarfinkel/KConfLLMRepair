from src.experiment import experiment_metrics, DriveUploader, sampler
from .repair import repair_config, get_input
from src.utils import log, dispatcher
from src.config import settings
from src.models import Sample
import click

def repair_all(samples: list[Sample], drive: DriveUploader | None = None):

    log.info('Starting repair of all samples...')

    tasks = [lambda i=i, s=sample: repair_sample(i, s, drive) for i, sample in enumerate(samples)]
    dispatcher.run_tasks(tasks, desc='Repairing samples')

def repair_sample(i: int, sample: Sample, drive: DriveUploader | None = None):

    log.info(f'Starting repair for sample {i + 1}...')

    input = get_input(config=sample.original_config, output=f'{settings.runtime.OUTPUT_DIR}/sample_{i}')

    repair_config(input, sample.kernel_src, lambda session: repair_callback(i, session, drive))

def repair_callback(i: int, session, drive: DriveUploader | None = None):
    experiment_metrics.record(i, session)
    if drive:
        drive.upload_results_json()

def run_experiment(n: int, skip_generation: bool, skip_repair: bool, drive: DriveUploader | None = None):

    log.info(f'Starting experiment with {n} samples...')

    if skip_generation and not skip_repair:
        log.info('Reading existing samples from sample folder...')
        samples = sampler.read_samples(n)
        repair_all(samples, drive)
    elif not skip_generation:
        log.info('Generating new samples...')

        callback = None if skip_repair else lambda i, s: repair_sample(i, s, drive)
        sampler.random(n, callback)
    else:
        log.info('Skipping both sample generation and repair phases.')

@click.command()
@click.option('-n', default=10, help='Number of samples to generate.')
@click.option('--jobs', '-j', default=8, help='Number of parallel jobs to use for building kernels.')
@click.option('--model', '-m', default='gemini-3-pro-preview', help='Override the default LLM model to use for repair.')
@click.option('--max-iterations', default=20, help='Maximum number of repair iterations per sample.')
@click.option('--max-threads', '-t', default=1, help='Maximum number of samples generating at once.')
@click.option('--skip-generation', is_flag=True, help='Skip the sample generation phase and only perform repair on existing samples.')
@click.option('--skip-repair', is_flag=True, help='Skip the sample generation phase and only perform repair on existing samples.')
@click.option('--cleanup', is_flag=True, help='Clean up kernel worktrees after processing samples.')
@click.option('--rag', is_flag=True, help='Use RAG semantic search instead of grep/chunk tools.')
@click.option('--drive', is_flag=True, help='Upload results to Google Drive after each repair.')
@click.option('--arch', '-a', default=None, help='Target kernel architecture (e.g. x86_64, arm64). Defaults to $ARCH env var or x86_64.')
def main(n: int, model: str, jobs: int, max_threads: int, max_iterations: int, skip_generation: bool, skip_repair: bool, cleanup: bool, rag: bool, drive: bool, arch: str | None):

    settings.runtime.MAX_THREADS = max_threads
    settings.agent.MODEL = model
    settings.runtime.JOBS = jobs
    settings.agent.MAX_ITERATIONS = max_iterations
    settings.runtime.CLEANUP = cleanup
    settings.runtime.USE_RAG = rag
    
    if arch is not None:
        settings.kernel.ARCH = arch

    run_experiment(n, skip_generation, skip_repair, DriveUploader() if drive else None)

if __name__ == '__main__':
    main()
