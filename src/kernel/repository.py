from src.config import settings
from src.utils import log
from git import Repo
import os

class KernelRepo:

    main_repo: Repo = Repo(settings.kernel.KERNEL_SRC)

    def __init__(self, kernel_src: str):

        self.repo = Repo(kernel_src)
        self.path = kernel_src

    def make_patch(self, output_dir: str, start_commit: str | None = None) -> tuple[bool, str | None]:

        end = self.repo.head.commit

        if start_commit:
            start = self.repo.commit(start_commit)
        else:
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
    def create_worktree(commit: str) -> str:

        path = f'{settings.kernel.WORKTREE_DIR}/{commit[:12]}'
        if os.path.exists(path):
            return path

        log.info('Creating worktree.')

        KernelRepo.main_repo.git.worktree('add', '-f', path, commit)

        log.success('Worktree created successfully.')

        return path
    
    @staticmethod
    def cleanup(path: str):

        # if path == settings.kernel.KERNEL_SRC:
        #     log.info('Cannot clean up the main kernel source directory. Skipping cleanup.')
        #     return
        
        log.info('Cleaning up worktree.')
        
        # try:

        #     KernelRepo.__main_repo.git.worktree('remove', '-f', path)
        #     log.success('Worktree removed from git tracking.')

        # except Exception as e:

        #     log.error(f'git worktree remove failed: {e}')

        #     if os.path.exists(path):
        #         try:
        #             log.info('Removing worktree directory manually.')
        #             shutil.rmtree(path)
        #             log.success('Worktree directory removed.')
        #         except Exception as rm_err:
        #             log.error(f'Error removing worktree directory: {rm_err}')
            
        #     try:

        #         KernelRepo.__main_repo.git.worktree('prune')
        #         log.info('Pruned stale worktree references.')
                
        #     except Exception as prune_err:
        #         log.error(f'git worktree prune failed: {prune_err}')
        
        # if path in active_kernels:
        #     del active_kernels[path]
