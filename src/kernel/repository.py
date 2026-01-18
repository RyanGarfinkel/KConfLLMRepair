from src.config import settings
from src.utils import log
from git import Repo
import shutil
import atexit
import sys
import os

active_kernels = {}
def handler():

    global active_kernels
    
    for path in active_kernels.keys():
        KernelRepo.cleanup(path)

atexit.register(handler)

class KernelRepo:

    __main_repo: Repo = Repo(settings.kernel.KERNEL_SRC)

    def __init__(self, kernel_src: str):

        self.repo = Repo(kernel_src)
        self.path = kernel_src

    def get_kernel_version(self) -> str:

        version = ''
        patchlevel = ''
        sublevel = ''
        extraversion = ''

        with open(f'{self.path}/Makefile', 'r') as f:
            for line in f:
                if line.startswith('VERSION'):
                    version = line.split('=')[1].strip()
                elif line.startswith('PATCHLEVEL'):
                    patchlevel = line.split('=')[1].strip()
                elif line.startswith('SUBLEVEL'):
                    sublevel = line.split('=')[1].strip()
                elif line.startswith('EXTRAVERSION'):
                    extraversion = line.split('=')[1].strip()

        return f'{version}.{patchlevel}.{sublevel}{extraversion}'

    def make_patch(self, output_dir: str) -> tuple[bool, str | None]:

        end = self.repo.head.commit

        commits = list(self.repo.iter_commits(end, max_count=settings.runtime.COMMIT_WINDOW))

        if not commits:
            log.info(f'No commits found for commit {self.commit}. Cannot create patch.')
            return False, None

        start = commits[-1]

        patch = self.repo.git.diff(f'{start.hexsha}..{end.hexsha}')
        patch_file = f'{output_dir}/changes.patch'

        if not patch:
            log.info(f'No changes found between {start.hexsha} and {end.hexsha}. Cannot create patch.')
            return False, None

        with open(patch_file, 'w') as f:
            f.write(patch)

        return True, start.hexsha

    @staticmethod
    def get_sample_ends(n: int, start_commit: str | None = None) -> list[str]:
        
        repo = KernelRepo.__main_repo

        if start_commit:
            end = repo.commit(start_commit)
        else:
            end = repo.head.commit

        commits = [end.hexsha]

        for _ in range(n - 1):

            start = list(repo.iter_commits(end, max_count=settings.runtime.COMMIT_WINDOW))[-1]
            start = start.parents[0]

            commits.append(start.hexsha)
            end = start

        return commits
    
    @staticmethod
    def create_worktree(commit: str) -> str:

        path = f'{settings.runtime.WORKTREE_DIR}/{commit[:12]}'
        if os.path.exists(path):
            log.info('Worktree already exists. Cleaning up before creating a new one.')
            KernelRepo.cleanup(path)

        log.info('Creating worktree.')

        KernelRepo.__main_repo.git.worktree('add', '-f', path, commit)

        log.success('Worktree created successfully.')
        active_kernels[path] = True

        return path
    
    @staticmethod
    def cleanup(path: str):

        if path == settings.kernel.KERNEL_SRC:
            log.info('Cannot clean up the main kernel source directory. Skipping cleanup.')
            return
        
        try:
            log.info('Cleaning up worktree.')

            KernelRepo.__main_repo.git.worktree('remove', '-f', path)
            if path in active_kernels:
                del active_kernels[path]
        except Exception as e:
            log.error(f'Error cleaning up worktree: {e}')
        finally:

            if not os.path.exists(path):
                return
            try:
                log.info('Removing worktree directory.')
                shutil.rmtree(path)
                log.success('Worktree directory removed successfully.')
            except Exception as e:
                log.error(f'Error removing worktree directory: {e}')
