from .repair import repair_config, get_input
from src.models import Sample
from .sample import generate_samples
from src.utils import dispatcher
from src.config import settings
from src.utils import file_lock
from src.agent import Session
from src.utils import log
import click
import json

completed_sessions: list[tuple[int, Session]] = []

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

    input = get_input(config=sample.config, output=f'{settings.runtime.SAMPLE_DIR}/sample_{i}')

    repair_config(input, sample.kernel_src, lambda session: repair_callback(i, session))

def repair_callback(i: int, session: Session):
    completed_sessions.append((i, session))

    sessions = [s for _, s in completed_sessions]
    n = len(sessions)
    successes = [s for s in sessions if s.status in ['success', 'success-maintenance']]

    avg_constraints = (
        sum(s.constraints['total'] for s in successes) / len(successes)
        if successes else -1
    )

    sorted_sessions = sorted(completed_sessions, key=lambda t: t[0])

    with file_lock:
        with open(f'{settings.runtime.SAMPLE_DIR}/results.json', 'w') as f:
            json.dump({
                'summary': {
                    'n': n,
                    'successes': len([s for s in sessions if s.status == 'success']),
                    'maintenance': len([s for s in sessions if s.status == 'success-maintenance']),
                    'failures': len([s for s in sessions if s.status == 'max-attempts-reached']),
                    'initial_input_worked': len([s for s in sessions if len(s.attempts) == 1 and s.status == 'success']),
                    'avg_attempts': sum(len(s.attempts) for s in sessions) / n if n > 0 else -1,
                    'avg_edit_distance': sum(s.edits[1] for s in successes) / len(successes) if successes else -1,
                    'avg_constraints': avg_constraints,
                },
                'llm_token_usage': {
                    'model': settings.agent.MODEL,
                    'input_tokens': sum(s.token_usage.input_tokens for s in sessions),
                    'output_tokens': sum(s.token_usage.output_tokens for s in sessions),
                    'total_tokens': sum(s.token_usage.total_tokens for s in sessions),
                },
                'embedding_token_usage': {
                    'model': settings.agent.EMBEDDING_MODEL if settings.runtime.USE_RAG else None,
                    'build_log_tokens': sum(s.embedding_usage.build_log_tokens for s in sessions),
                    'boot_log_tokens': sum(s.embedding_usage.boot_log_tokens for s in sessions),
                    'total_tokens': sum(s.embedding_usage.total_tokens for s in sessions),
                },
                'samples': [
                    {
                        'sample': idx + 1,
                        'status': s.status,
                        'attempts': len(s.attempts),
                        'edit_distance': s.edits[1] if s.edits else -1,
                        'constraints': s.constraints,
                        'llm_token_usage': s.token_usage.model_dump(),
                        'embedding_token_usage': s.embedding_usage.model_dump(),
                    } for idx, s in sorted_sessions
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
@click.option('--max-iterations', default=5, help='Maximum number of repair iterations per sample.')
@click.option('--max-threads', '-t', default=8, help='Maximum number of samples generating at once.')
@click.option('--skip-generation', is_flag=True, help='Skip the sample generation phase and only perform repair on existing samples.')
@click.option('--skip-repair', is_flag=True, help='Skip the sample generation phase and only perform repair on existing samples.')
@click.option('--cleanup', is_flag=True, help='Clean up kernel worktrees after processing samples.')
@click.option('--rag', is_flag=True, help='Use RAG semantic search instead of grep/chunk tools.')
def main(n: int, model: str, jobs: int, max_threads: int, max_iterations: int, skip_generation: bool, skip_repair: bool, cleanup: bool, rag: bool):

    settings.runtime.MAX_THREADS = max_threads
    settings.agent.MODEL = model
    settings.runtime.JOBS = jobs
    settings.agent.MAX_ITERATIONS = max_iterations
    settings.runtime.CLEANUP = cleanup
    settings.runtime.USE_RAG = rag

    run_experiment(n, skip_generation, skip_repair)

if __name__ == '__main__':
    main()
