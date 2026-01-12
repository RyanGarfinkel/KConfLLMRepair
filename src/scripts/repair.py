from src.agents import factory, Agent
from src.tools import AgentTools
from src.config import settings
from src.core import Kernel
from src.models import Sample
from src.utils import log
import signal
import click
import sys

active_kernel = None
def handler(a, b):

    global active_kernel
    
    if active_kernel is not None:
        log.info('Cleaning up active kernel worktree...')
        active_kernel.cleanup()
    
    sys.exit(0)

signal.signal(signal.SIGINT, handler)

def repair_sample(sample: Sample, llm, max_iterations: int):

    global active_kernel

    active_kernel = kernel = Kernel(sample.end_commit)
    tools = AgentTools(kernel, sample)

    agent = Agent(llm, tools=tools.get_tools(), max_iterations=max_iterations)

    result = agent.run()

    kernel.cleanup()
    active_kernel = None

    return result

def repair_all(n: int, model: str, max_iterations: int):


    llm = factory.get_llm(model)
    results = []

    samples = Sample.get_samples(n)

    for i, sample in enumerate(samples):
        
        log.info(f'Starting repair for sample {i+1}/{n}: {sample.dir}')

        result = repair_sample(sample, llm, max_iterations)
        results.append(result)
        
        log.info(f'Finished repair for sample {i+1}/{n}: {sample.dir}')

    print()
    print()
    print()
    for i, result in enumerate(results):
        print(f'Sample {i+1}/{n}:')
        print(result)
        print()
        print()

@click.command()
@click.option('--n', default=1, help='Number of samples to repair')
@click.option('--model', default='gpt-4o-mini', help='LLM model to use for repair')
@click.option('--max_iterations', default=10, help='Maximum number of iterations for the agent to perform')
def main(n: int, model: str, max_iterations: int):
    repair_all(n, model, max_iterations)

if __name__ == '__main__':
    main()
