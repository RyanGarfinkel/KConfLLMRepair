from src.utils.log import log_error, log_info, log_success
from singleton_decorator import singleton
from src.kernel.kconfig import KConfig
from src.config import kernel_src
from datetime import timedelta
from git import Repo
import subprocess
import os

_COMMIT_WINDOW = 25

@singleton
class KernelRepo:

    def __init__(self):

        if not os.path.exists(kernel_src):
            raise FileNotFoundError(f'Kernel source path not found at {kernel_src}')
        
        self._repo = Repo(kernel_src)
        self._end_commit = self._repo.head.commit
    
    def clean(self) -> bool:
        
        self._repo.git.reset('--hard')
        self._repo.git.clean('-fdx')

    def checkout(self, commit) -> bool:
        
        try:
            self.clean()
            self._repo.git.checkout(commit.hexsha)
            return True
        except Exception as e:
            log_error(f'Failed to checkout commit {commit.hexsha}: {e}')
            return False
        
    def checkout_tag(self, tag_name: str) -> bool:

        log_info(f'Checking out tag {tag_name}...')
        try:
            self.clean()
            self._repo.git.checkout(tag_name)
            return True
        except Exception as e:
            log_error(f'Failed to checkout tag {tag_name}: {e}')
            return False

    def fetch_history_tag(self) -> bool:
        """
        Pre-fetches linux-next tags based on the CURRENT HEAD of the repo.
        """
        # 1. IGNORE the argument. Look at what is actually checked out.
        # This fixes the mismatch between Python's view and syz-kconf's view.
        target_date = self._repo.head.commit.committed_datetime
        
        # 2. Shotgun approach: Try Target Date +/- 1 Day to handle timezone diffs
        dates_to_try = [
            target_date, 
            target_date + timedelta(days=1), 
            target_date - timedelta(days=1)
        ]

        # 3. Setup Remote
        history_url = 'https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next-history.git'
        try:
            if 'linux-next-history' not in self._repo.remotes:
                self._repo.create_remote('linux-next-history', history_url)
        except Exception as e:
            log_error(f'Failed to setup remote: {e}')
            return False

        success = False
        for date_obj in dates_to_try:
            tag_name = f"next-{date_obj.strftime('%Y%m%d')}"
            
            # Check local existence
            try:
                self._repo.git.show(tag_name, '--stat')
                if date_obj == target_date:
                    log_info(f'Tag {tag_name} exists locally.')
                success = True
                continue 
            except Exception:
                pass 

            # Fetch
            log_info(f'Fetching tag candidate {tag_name} via HTTPS...')
            try:
                self._repo.git.fetch('linux-next-history', 'tag', tag_name, '--no-tags')
                log_success(f'Successfully fetched {tag_name}')
                success = True
            except Exception:
                pass
        
        return success
    
    def get_commit_window(self, n=_COMMIT_WINDOW):

        commits = []
        current_commit = self._end_commit

        for _ in range(n):
            commits.append(current_commit)
            if not current_commit.parents:
                break
            current_commit = current_commit.parents[0]
        
        return commits
    
    def diff(self, start_commmit, end_commit):
         
         return self._repo.git.diff(f'{start_commmit.hexsha}..{end_commit.hexsha}')
