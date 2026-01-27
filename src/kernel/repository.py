from src.config import settings
from src.utils import log
from git import Repo
import shutil
import atexit
import re
import os

active_kernels = {}
def handler():

    global active_kernels
    
    for path in list(active_kernels.keys()):
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

        patch = self.repo.git.log('-p', '--no-merges', f'{start.hexsha}..{end.hexsha}')
        patch_file = f'{output_dir}/changes.patch'

        if not patch:
            log.info(f'No changes found between {start.hexsha} and {end.hexsha}. Cannot create patch.')
            return False, None

        with open(patch_file, 'w') as f:
            f.write(patch)

        return True, start.hexsha

    def get_option_mapping(self) -> dict[str, list[str]]:

        map = {}

        for path, dirs, files in os.walk(f'{self.path}'):

            if 'Kconfig' not in files:
                continue

            with open(f'{path}/Kconfig', 'r') as f:
                subgroup = os.path.basename(path)
                options = []
                for line in f:
                    match = re.search(r'config (\w+)', line)
                    if match:
                        options.append(match.group(1))

                if options:
                    map[subgroup] = options

        return map

    def __parse_kconfig(path: str) -> dict[str, list[str]]:

        map = {}
        menu = 'placeholder'

        with open(path, 'r') as f:
            for line in f:
                line = line.strip()

                if line.startswith('menu '):
                    menu = line.split('menu ')[1].strip().strip('"')
                elif line.startswith('config '):
                    option = line.split('config ')[1].strip()
                    if menu not in map:
                        map[menu] = []
                    map[menu].append(option)
                elif line.startswith('endmenu'):
                    menu = 'placeholder'

        return map

    @staticmethod
    def get_sample_ends(n: int, start_commit: str | None = None) -> list[str]:
        
        repo = KernelRepo.__main_repo

        if start_commit:
            end = repo.commit(start_commit)
        else:
            end = repo.head.commit

        commits = [end.hexsha]

        for _ in range(n - 1):

            start = list(repo.iter_commits(end, max_count=settings.runtime.COMMIT_WINDOW, no_merges=True))[-1]
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
        
        # log.info('Cleaning up worktree.')
        
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
