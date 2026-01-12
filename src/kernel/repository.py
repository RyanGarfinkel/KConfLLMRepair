from src.config import settings
from src.utils import log
from git import Repo
import shutil
import os

class KernelRepo:

    __main_repo: Repo | None = None

    def __init__(self, commit: str):

        self.__load_main_repo()

        self.commit = commit
        self.path = f'{settings.WORKTREE_DIR}/{commit[:12]}'
        
        self.__create_worktree()

    def __load_main_repo(self):
        if KernelRepo.__main_repo is None:
            KernelRepo.__main_repo = Repo(settings.KERNEL_SRC)

    def __create_worktree(self):

        log.info(f'Creating worktree for commit {self.commit}.')

        if os.path.exists(self.path):
            log.info(f'Worktree for commit {self.commit} already exists. Cleaning up before creating a new one.')
            self.cleanup()

        KernelRepo.__main_repo.git.worktree('add', '-f', self.path, self.commit)
        self.repo = Repo(self.path)

        log.success(f'Worktree for commit {self.commit} created successfully.')

    def make_patch(self, output_dir: str, commit_window: int) -> (bool, str | None):

        log.info(f'Creating patch for commit {self.commit}.')

        end = self.repo.head.commit

        commits = list(self.repo.iter_commits(end, max_count=commit_window))

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

        log.success(f'Patch for commit {self.commit} created successfully at {patch_file}.')

        return True, start.hexsha

    def cleanup(self):

        try:
            log.info(f'Cleaning up worktree for commit {self.commit}.')

            KernelRepo.__main_repo.git.worktree('remove', '-f', self.path)
        except Exception as e:
            log.error(f'Error cleaning up worktree for commit {self.commit}: {e}')
        finally:

            if not os.path.exists(self.path):
                return

            try:
                log.info(f'Removing worktree directory for commit {self.commit}.')
                shutil.rmtree(self.path)
                log.success(f'Worktree directory for commit {self.commit} removed successfully.')
            except Exception as e:
                log.error(f'Error removing worktree directory for commit {self.commit}: {e}')
