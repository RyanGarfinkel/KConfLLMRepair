from singleton_decorator import singleton
from src.config import settings
from src.utils import log
from git import Repo
import atexit
import shutil
import os

active_kernels = {}
def handler():

    global active_kernels

    log.info('Cleaning up active worktrees...')
    
    # for path in list(active_kernels.keys()):
    #     worktree.cleanup(path)

    log.info('Worktree cleanup complete.')

atexit.register(handler)

@singleton
class Worktree:

    def __init__(self):
        self.main_repo = Repo(settings.kernel.KERNEL_SRC)
    
    def create(self, commit: str) -> str:

        path = f'{settings.kernel.WORKTREE_DIR}/{commit[:10]}'

        if os.path.exists(path):
            log.info(f'Worktree for commit {commit[:10]} already exists...')
            return path
        
        log.info(f'Creating worktree for commit {commit[:10]}...')
        self.main_repo.git.worktree('add', '-f', path, commit)
        log.success('Worktree created successfully.')

        active_kernels[path] = True

        return path
    
    def cleanup(self, path: str) -> bool:

        if not os.path.exists(path):
            return True
        
        if path == settings.kernel.KERNEL_SRC:
            log.info('Skipping cleanup of main kernel source directory.')
            return True
        
        log.info(f'Cleaning up worktree at {path}...')

        if path in active_kernels:
            del active_kernels[path]

        try:
            self.main_repo.git.worktree('remove', '-f', path)
            log.success('Worktree removed from git tracking.')
            return True
        except Exception as e:
            log.error(f'Failed to remove worktree via git: {e}')
            log.info('Attempting manual removal of worktree directory.')

            try:
                shutil.rmtree(path)
                log.success('Worktree directory removed manually.')
                return True
            except Exception as rm_err:
                log.error(f'Error removing worktree directory: {rm_err}')
                return False

worktree = Worktree()
