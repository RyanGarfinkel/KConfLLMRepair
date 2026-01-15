from src.models import AgentResult
from src.core.agent import Agent
from src.models import Sample
from src.utils import log
import click

def repair_samples(n: int, model_override: str | None = None):


    agent = Agent(model_override)
    samples = Sample.get_samples(n)

    results = []

    for i, sample in enumerate(samples):

        log.info(f'Repairing sample {i + 1}...')

        result = agent.repair(sample)
        
        results.append(result)
        AgentResult.save_results(results)

@click.command()
@click.option('--n', default=10, help='Number of samples to repair.')
@click.option('--model-override', default=None, help='Override the default LLM model to use for repair.')
def main(n: int, model_override: str | None = None):

    log.info(f'Starting repair process for {n} samples...')

    if model_override:
        log.info(f'Using model override: {model_override}')
    else:
        log.info('Using default model based on available API keys.')

    repair_samples(n, model_override)

    log.info('Repair process completed.')

if __name__ == '__main__':
    main()