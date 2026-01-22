from src.core import Agent, Kernel
from src.config import settings
from src.models import Sample
from src.utils import log
import shutil
import click
import os

def initial_attempt(sample: Sample) -> bool:

    log.info('Verifying modified configuration does not boot...')

    attempt_dir = f'{sample.output}/attempt_0'
    if os.path.exists(attempt_dir):
        shutil.rmtree(attempt_dir)

    # Setup attempt_0 directory
    os.makedirs(attempt_dir, exist_ok=True)
    shutil.copy(sample.base, f'{attempt_dir}/base.config')
    shutil.copy(sample.modified, f'{attempt_dir}/modified.config')
    shutil.copy(sample.patch, f'{attempt_dir}/changes.patch')

    # Building the kernel
    kernel = Kernel(sample.kernel_src)
    if not kernel.build(sample.modified, f'{attempt_dir}/build.log'):
        log.info('Build failed. Will proceed with agent repair.')
        return True
    
    # Booting the kernel
    if not kernel.boot(f'{attempt_dir}/qemu.log'):
        log.info('Boot failed. Will proceed with agent repair.')
        return True
    
    log.info('Modified configuration boots successfully. No repair needed.')
    
    return False

def repair(sample: Sample, model: str | None):

    if not initial_attempt(sample):
        return

    log.info('Creating agent for repair process...')
    
    agent = Agent(model)

    log.success('Agent created successfully.')
    log.info('Starting repair process...')

    result = agent.repair(sample)

    log.info('Repair process completed. Saving results...')

    result.save(f'{sample.output}/result.json')

@click.command()
@click.option('--base', required=True, help='Path to the original configuration file.')
@click.option('--modified', required=True, help='Path to the modified configuration file.')
@click.option('--patch', required=True, help='Path to the patch file that the modification tries to include.')
@click.option('--output', default=None, help='Path to direct the agent attempts and results, otherwise set to the current working directory.')
@click.option('--kernel-src', default=None, help='Path to the kernel source code, otherwise set to the environment variable KERNEL_SRC.')
@click.option('--model', default=None, help='Model name of you wish to use for repair, otherwise set to a default model based on available API keys.')
@click.option('--max-iterations', default=5, help='Maximum number of iterations for the agent to attempt repairs, otherwise set to 5.')
@click.option('--jobs', default=None, help='Number of jobs to run when building the kernel, otherwise set to 8.')
def main(base: str, modified: str, patch: str, output: str | None, kernel_src: str | None, model: str | None, jobs: int | None, max_iterations: int):

    # Validate inputs
    if not os.path.exists(base):
        raise ValueError(f'Base configuration file {base} does not exist.')
    
    if not os.path.exists(modified):
        raise ValueError(f'Modified configuration file {modified} does not exist.')
    
    if not os.path.exists(patch):
        raise ValueError(f'Patch file {patch} does not exist.')

    if output is None:
        output = os.getcwd() + '/agent-repair-attempts'
    
    if kernel_src is None:
        kernel_src = settings.kernel.KERNEL_SRC
    elif not os.path.exists(kernel_src):
        raise ValueError(f'Kernel source path {kernel_src} does not exist.')

    if jobs is not None:
        settings.kernel.JOBS = jobs

    settings.agent.MAX_ITERATIONS = max_iterations
    
    # Repair Process
    os.makedirs(output, exist_ok=True)
    
    sample = Sample(
        base=os.path.abspath(base),
        modified=os.path.abspath(modified),
        patch=os.path.abspath(patch),
        kernel_src=os.path.abspath(kernel_src),
        output=os.path.abspath(output) + '/agent-repair-attempts',
        commit=None
    )

    repair(sample, model)

if __name__ == '__main__':
    main()
