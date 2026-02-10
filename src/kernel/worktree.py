from singleton_decorator import singleton
from src.config import settings
from src.utils import log
from git import Repo
import shutil
import os

@singleton
class Worktree:

    def __init__(self):
        self.main_repo = Repo(settings.kernel.KERNEL_SRC)
    
    def create(self, commit: str) -> str:

        ending = 0
        path = f'{settings.kernel.WORKTREE_DIR}/{commit[:10]}_{ending}'
        while os.path.exists(path):
            ending += 1
            path = f'{settings.kernel.WORKTREE_DIR}/{commit[:10]}_{ending}'
        
        log.info(f'Creating worktree for commit {commit[:10]}...')
        self.main_repo.git.worktree('add', '-f', path, commit)
        log.success('Worktree created successfully.')
        
        log.info('Ensuring worktree is checked out at end commit...')
        tmp_repo = Repo(path)
        tmp_repo.git.checkout(commit, force=True)
        log.info('Worktree checkout complete.')

        return path
    
    def cleanup(self, path: str) -> bool:

        if not os.path.exists(path):
            return True
        
        if path == settings.kernel.KERNEL_SRC:
            log.info('Skipping cleanup of main kernel source directory.')
            return True
        
        log.info(f'Cleaning up worktree at {path}...')

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
