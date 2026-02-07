from src.models import Input, State
from src.core.kernel import Kernel
from src.config import settings
from src.llm import Session
from typing import Callable
from src.core import agent
from src.utils import log
import shutil
import click
import os

def repair(input: Input, kernel_src: str, complete_callback: Callable[[State, Session], None] | None = None):

    kernel = Kernel(kernel_src)

    log.info('Starting agent repair process...')

    final_state, session = agent.repair(input, kernel)

    if final_state.get('verify_succeeded', False):
        log.success('Agent repair repaired the configuration successfully.')
        log.info(f'Saving repaired configuration to {input.output_dir}/repaired.config')
        shutil.copyfile(final_state.get('modified_config'), f'{input.output_dir}/repaired.config')
    else:
        log.error('Agent repair failed to repair the configuration.')

    log.info(f'See {input.output_dir} for full details of the agent repair attempts.')

    if complete_callback is not None:
        complete_callback(final_state, session)

@click.command()
@click.option('--base', required=True, help='Path to the original configuration file.')
@click.option('--modified', required=True, help='Path to the modified configuration file.')
@click.option('--patch', required=True, help='Path to the patch file that the modification tries to include.')
@click.option('--output', default=None, help='Path to direct the agent attempts and results, otherwise set to the current working directory.')
@click.option('--kernel-src', default=None, help='Path to the kernel source code, otherwise set to the environment variable KERNEL_SRC.')
@click.option('--model', default='gemini-3-pro-preview', help='Model name of you wish to use for repair.')
@click.option('--jobs', '-j', default=8, help='Number of jobs to run when building the kernel.')
def main(base: str, modified: str, patch: str, output: str | None, kernel_src: str | None, model: str, jobs: int):

    input = Input(
        base_config=base,
        modified_config=modified,
        patch=patch,
        output_dir=output
    )

    settings.runtime.JOBS = jobs
    settings.agent.MODEL = model
    # MAX_VERIFY_ATTEMPTS
    # MAX_KLOCALIZER_RUNS
    # MAX_TOOL_CALLS
    
    if kernel_src is None:
        kernel_src = settings.kernel.KERNEL_SRC
    elif not os.path.exists(kernel_src):
        raise ValueError(f'Kernel source path {kernel_src} does not exist.')

    repair(input, kernel_src)

if __name__ == '__main__':
    main()
