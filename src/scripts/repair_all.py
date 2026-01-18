from src.kernel import KernelRepo
from src.config import settings
from git import Repo
import subprocess
import os


path = '/home/ubuntu/KConfLLMRepair/workspace/samples/sample_0'

base = f'{path}/base.config'
modified = f'{path}/modified.config'
patch = f'{path}/changes.patch'

repo = Repo(settings.kernel.KERNEL_SRC)
commit = repo.commit('HEAD').hexsha

kernel_src = KernelRepo.create_worktree(commit)

subprocess.run(['python3', '-m', 'src.scripts.repair', '--base', base, '--modified', modified, '--patch', patch, '--kernel-src', kernel_src], check=True)

KernelRepo.cleanup(kernel_src)
