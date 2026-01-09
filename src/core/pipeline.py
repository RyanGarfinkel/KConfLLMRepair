from src.utils.log import log_info, log_success, log_error
from src.kernel.repository import KernelRepo
from src.llm.toolbox import get_agent_tools
from src.tools.klocalizer import KLocalizer
from src.tools.syzkaller import Syzkaller
from src.kernel.kconfig import KConfig
from src.kernel.builder import Builder
from src.kernel.boot import does_boot
from src.models.sample import Sample
from src.llm.agent import Agent
from dotenv import load_dotenv
import subprocess
import os

load_dotenv()

_BASE_CONFIG = os.getenv('BASE_CONFIG')
if not _BASE_CONFIG:
    raise EnvironmentError('BASE_CONFIG not set.')

if not os.path.exists(_BASE_CONFIG):
    raise FileNotFoundError(f'Base config file not found at {_BASE_CONFIG}')

def generate_sample(dir, commit):

    os.makedirs(dir, exist_ok=True)

    repo = KernelRepo(commit)
    klocalizer = KLocalizer()
    builder = Builder()

    # Build the patch
    start, end, patch = repo.build_patch(dir)

    result = Sample(start_commit=start.hexsha, end_commit=end.hexsha, patch=patch, config=None, build_log=None, qemu_boot_result=None)

    # Copy base config
    base_config = KConfig(_BASE_CONFIG)
    base_config.cp(f'{repo.path}/.config')

    # Run KLocalizer
    klocalizer_config = klocalizer.repair(repo.path, dir)
    if klocalizer_config is None:
        log_error('KLocalizer repair failed. Aborting sample generation.')
        return result
    
    if not builder.make_olddefconfig(repo):
        return result

    klocalizer_config.cp(f'{dir}/klocalizer.config')
    result.config = f'{dir}/klocalizer.config'

    # Buid the kernel with updated config
    bzImg, build_log = builder.build_kernel(repo, dir)
    if not bzImg:
        return result

    result.build_log = build_log

    # QEMU test
    result.qemu_boot_result = does_boot(bzImg, dir)

    # Finish
    log_info('Sample generation complete.')

    return result

def repair_sample(sample, dir):

    # Setup
    log_info('Setting up LLM Agent for sample repair...')

    repo = KernelRepo(sample.end_commit)
    tools = get_agent_tools(repo, dir)

    agent = Agent(dir, tools)

    # Repair
    log_info('Starting sample repair...')

    success = agent.repair()

    # TODO: Track agent process and results, # of iterations, etc.
    # TODO: Find better way to track success and failure.

    # Final
    if success:
        log_success('Sample repaired successfully!')
    else:
        log_error('Sample repair failed.')
