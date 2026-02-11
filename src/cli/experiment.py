from src.models import Sample, Input
from .sample import generate_samples
from .repair import repair_config
from src.utils import dispatcher
from src.config import settings
from src.utils import file_lock
from src.agent import Session
from src.utils import log
import click
import json

comleted_sessions = []

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
        config=sample.config,
        output=f'{settings.runtime.SAMPLE_DIR}/sample_{i}'
    )

    repair_config(input, sample.kernel_src, repair_callback)

def repair_callback(session: Session):
        comleted_sessions.append(session)

        n = len(comleted_sessions)
        successes = [s for s in comleted_sessions if s.status == 'Success']

        with file_lock:
            with open(f'{settings.runtime.SAMPLE_DIR}/results.json', 'w') as f:
                json.dump({
                    'summary': {
                        'n': n,
                        'successes': len([s for s in comleted_sessions if s.status == 'Success']),
                        'failures': len([s for s in comleted_sessions if s.status != 'Success']),
                        'input_worked': len([s for s in comleted_sessions if len(s.attempts) == 1 and s.status == 'Success']),
                        'avg_attempts': sum(len(s.attempts) for s in comleted_sessions) / n if n > 0 else -1,
                        'avg_edit_distance': sum(s.edits[1] for s in successes) / len(successes) if len(successes) > 0 else -1
                    },
                    'token_usage': {
                        'input_tokens': sum(s.attempts[-1].token_usage.input_tokens for s in comleted_sessions),
                        'output_tokens': sum(s.attempts[-1].token_usage.output_tokens for s in comleted_sessions),
                        'total_tokens': sum(s.attempts[-1].token_usage.total_tokens for s in comleted_sessions),
                    },
                    'samples': [
                        {
                            'status': s.status,
                            'attempts': len(s.attempts),
                            'edit_distance': s.edits[1] if s.edits else -1,
                        } for s in comleted_sessions
                    ]
                }, f, indent=4)

def run_experiment(n: int, skip_generation: bool, skip_repair: bool):

    log.info(f'Starting experiment with {n} samples...')

    if skip_generation and not skip_repair:
        log.info('Reading existing samples from sample folder...')
        samples = read_samples(n)
        repair_all(samples)
    elif not skip_generation:
        log.info('Generating new samples...')

        callback = None if skip_repair else repair_sample
        generate_samples(n, callback)
    else:
        log.info('Skipping both sample generation and repair phases.')

@click.command()
@click.option('-n', default=10, help='Number of samples to generate.')
@click.option('--jobs', '-j', default=8, help='Number of parallel jobs to use for building kernels.')
@click.option('--model', '-m', default='gemini-3-pro-preview', help='Override the default LLM model to use for repair.')
@click.option('--max-threads', '-t', default=8, help='Maximum number of samples generating at once.')
@click.option('--skip-generation', is_flag=True, help='Skip the sample generation phase and only perform repair on existing samples.')
@click.option('--skip-repair', is_flag=True, help='Skip the sample generation phase and only perform repair on existing samples.')
@click.option('--cleanup', is_flag=True, help='Clean up kernel worktrees after processing samples.')
def main(n: int, model: str, jobs: int, max_threads: int, skip_generation: bool, skip_repair: bool, cleanup: bool):

    settings.runtime.MAX_THREADS = max_threads
    settings.agent.MODEL = model
    settings.runtime.JOBS = jobs
    settings.runtime.CLEANUP = cleanup

    run_experiment(n, skip_generation, skip_repair)

if __name__ == '__main__':
    main()
