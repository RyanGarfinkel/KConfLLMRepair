from src.core.kernel import Kernel
from src.config import settings
from src.agent import Session
from src.models import Input
from typing import Callable
from src.core import agent
from src.utils import log
import click
import os

def repair(input: Input, kernel_src: str, complete_callback: Callable[[Session], None] | None = None):

    kernel = Kernel(kernel_src)

    log.info('Starting agent repair process...')

    session = agent.repair(input, kernel)

    log.info(f'See {input.output_dir} for full details of the agent repair attempts.')

    if complete_callback is not None:
        complete_callback(session)

@click.command()
@click.option('--repair', default=None, help='Path to configuration file to repair.')
@click.option('--base', default=None, help='Path to the original configuration file.')
@click.option('--modified', default=None, help='Path to the modified configuration file.')
@click.option('--patch', default=None, help='Path to the patch file that the modification tries to include.')
@click.option('--output', default=None, help='Path to direct the agent attempts and results, otherwise set to the current working directory.')
@click.option('--src', default=None, help='Path to the kernel source code, otherwise set to the environment variable KERNEL_SRC.')
@click.option('--model', default='gemini-3-pro-preview', help='Model name of you wish to use for repair.')
@click.option('--jobs', '-j', default=8, help='Number of jobs to run when building the kernel.')
def main(repair: str | None, base: str | None, modified: str | None, patch: str | None, output: str | None, src: str | None, model: str, jobs: int):

    # Assertions & Input
    if patch is None:
        assert repair is not None
        assert base is None
        assert modified is None
        
        input = Input(
            base_config=repair,
            modified_config=repair,
            patch=None,
            output_dir=output
        )
    else:
        assert repair is None
        assert base is not None
        assert modified is not None

        input = Input(
            base_config=base,
            modified_config=modified,
            patch=patch,
            output_dir=output
        )

    settings.runtime.JOBS = jobs
    settings.agent.MODEL = model
    
    if src is None:
        src = settings.kernel.KERNEL_SRC
    elif not os.path.exists(src):
        raise ValueError(f'Kernel source path {src} does not exist.')

    repair(input, src)

if __name__ == '__main__':
    main()
