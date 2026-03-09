from src.core.kernel import Kernel
from src.config import settings
from src.agent import Session
from src.models import Input
from typing import Callable
from src.core import agent
from src.utils import log
import click
import os

def get_input(config: str | None = None, original: str | None = None, modified: str | None = None, patch: str | None = None, output: str | None = None) -> Input:

    patched_mode = any(v is not None for v in (original, modified, patch))

    if patched_mode and config is not None:
        raise click.UsageError('Use either --config or --original/--modified/--patch, not both.')

    if not patched_mode and config is None:
        raise click.UsageError('Provide either --config or --original/--modified/--patch.')

    if patched_mode and not all(v is not None for v in (original, modified, patch)):
        raise click.UsageError('--original, --modified, and --patch must be provided.')

    if patched_mode:
        return Input(original_config=original, modified_config=modified, patch=patch, output=output)
    
    return Input(original_config=config, output=output)

def repair_config(input: Input, kernel_src: str, complete_callback: Callable[[Session], None] | None = None):

    log.info('Starting agent repair process...')
    
    kernel = Kernel(kernel_src)

    session = agent.repair(input, kernel)

    log.info(f'See {input.output} for full details of the agent repair attempts.')

    if complete_callback is not None:
        complete_callback(session)

@click.command()
@click.option('--config', default=None, help='Path to a configuration file to repair.')
@click.option('--original', default=None, help='Path to the original (unmodified) config (use with --modified and --patch).')
@click.option('--modified', default=None, help='Path to the modified config derived from --original.')
@click.option('--patch', default=None, help='Path to the patch file that produced --modified from --original.')
@click.option('--output', default=None, help='Path to direct the agent attempts and results, otherwise set to the current working directory.')
@click.option('--src', default=None, help='Path to the kernel source code, otherwise set to the environment variable KERNEL_SRC.')
@click.option('--model', '-m', default='gemini-3-pro-preview', help='Model name of you wish to use for repair.')
@click.option('--jobs', '-j', default=8, help='Number of jobs to run when building the kernel.')
@click.option('--max-iterations', default=5, help='Maximum number of repair iterations per sample.')
@click.option('--rag', is_flag=True, help='Use RAG semantic search instead of grep/chunk tools.')
def main(config: str | None, original: str | None, modified: str | None, patch: str | None, output: str | None, src: str | None, model: str, jobs: int, max_iterations: int, rag: bool):

    input = get_input(config=config, original=original, modified=modified, patch=patch, output=output)

    settings.runtime.JOBS = jobs
    settings.runtime.USE_RAG = rag
    settings.agent.MODEL = model
    settings.agent.MAX_ITERATIONS = max_iterations

    if src is None:
        src = settings.kernel.KERNEL_SRC
    elif not os.path.exists(src):
        raise ValueError(f'Kernel source path {src} does not exist.')

    src = os.path.abspath(src)
    repair_config(input, src)

if __name__ == '__main__':
    main()
