from src.core.kernel import Kernel
from src.config import settings
from src.agent import Session
from src.models import Input
from typing import Callable
from src.core import agent
from src.utils import log
import click
import os

def repair_config(input: Input, kernel_src: str, complete_callback: Callable[[Session], None] | None = None):

    log.info('Starting agent repair process...')
    
    kernel = Kernel(kernel_src)

    session = agent.repair(input, kernel)

    log.info(f'See {input.output} for full details of the agent repair attempts.')

    if complete_callback is not None:
        complete_callback(session)

@click.command()
@click.option('--repair', required=True, help='Path to configuration file to repair.')
@click.option('--output', default=None, help='Path to direct the agent attempts and results, otherwise set to the current working directory.')
@click.option('--src', default=None, help='Path to the kernel source code, otherwise set to the environment variable KERNEL_SRC.')
@click.option('--model', '-m', default='gemini-3-pro-preview', help='Model name of you wish to use for repair.')
@click.option('--jobs', '-j', default=8, help='Number of jobs to run when building the kernel.')
@click.option('--max-iterations', default=5, help='Maximum number of repair iterations per sample.')
@click.option('--rag', is_flag=True, help='Use RAG semantic search instead of grep/chunk tools.')
@click.option('--arch', '-a', default=None, help='Target kernel architecture (e.g. x86_64, arm64). Defaults to $ARCH env var or x86_64.')
def main(repair: str, output: str | None, src: str | None, model: str, jobs: int, max_iterations: int, rag: bool, arch: str | None):

    input = Input(
        config=repair,
        output=output
    )

    settings.runtime.JOBS = jobs
    settings.runtime.USE_RAG = rag
    settings.agent.MODEL = model
    settings.agent.MAX_ITERATIONS = max_iterations

    if arch is not None:
        settings.kernel.ARCH = arch
        os.environ['ARCH'] = arch

    if src is None:
        src = settings.kernel.KERNEL_SRC
    elif not os.path.exists(src):
        raise ValueError(f'Kernel source path {src} does not exist.')

    src = os.path.abspath(src)
    repair_config(input, src)

if __name__ == '__main__':
    main()
