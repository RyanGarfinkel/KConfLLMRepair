from src.utils.log import log_info, log_error, log_success
from singleton_decorator import singleton
from src.kernel.kconfig import KConfig
from src.config import kernel_src
from git import Repo, Commit
import subprocess
import os

_PATH = '/home/dev/opt/syzkaller'
if not os.path.exists(_PATH):
    raise FileNotFoundError(f'Syzkaller path not found at {_PATH}')

_SYZ_KONF=f'{_PATH}/tools/syz-kconf'
if not os.path.exists(_SYZ_KONF):
    raise FileNotFoundError(f'Syz-kconf tool not found at {_SYZ_KONF}')

_MAIN_YML_PATH = f'{_PATH}/dashboard/config/linux/main.yml'
if not os.path.exists(_MAIN_YML_PATH):
    raise FileNotFoundError(f'Syzkaller config file not found at {_MAIN_YML_PATH}')

_BUILD_PATH = f'{_SYZ_KONF}/syz-kconf'

_CONFIG_PATH = f'{_PATH}/dashboard/config/linux/upstream-apparmor-kasan.config'

_REPO = Repo(_PATH)

@singleton
class Syzkaller:

    def __init__(self):
        self._build_path = None

    def _get_version(self, kernel_commit: Commit) -> Commit:

        kernel_commit_date = kernel_commit.committed_datetime

        try:
            commit = next(_REPO.iter_commits(until=kernel_commit_date))
            return commit
        except StopIteration:
            log_error('Failed to find syzkaller version for given kernel commit.')
            return None
        
    def build_for(self, kernel_commit: Commit) -> bool:

        syz_commit = self._get_version(kernel_commit)

        if syz_commit is None:
            return False
        
        log_info(f'Building syzkaller version {syz_commit.hexsha}')

        _REPO.git.reset('--hard')
        _REPO.git.clean('-fdx')
        _REPO.git.checkout(syz_commit.hexsha)

        result = subprocess.run('go build', cwd=_SYZ_KONF, shell=True, check=True)
        if result.returncode != 0:
            log_error('Failed to build syz-konf tool')
            return False
        
        self._build_path = _BUILD_PATH

        log_success(f'Successfully built syz-konf for kernel commit {kernel_commit.hexsha}')

        return True

    def generate_base_config(self) -> bool:

        if self._build_path is None:
            log_error('Syzkaller build path is not set. Please build syzkaller first.')
            return None
    
        log_info(f'Generating base config...')
        
        cmd = [
            self._build_path,
            '-config', _MAIN_YML_PATH,
            '-sourcedir', kernel_src,
            '-instance', 'upstream-apparmor-kasan',
            '-vv', '10'
        ]

        try:
            result = subprocess.run(
                cmd, 
                cwd=kernel_src, 
                check=True,
                text=True,
                capture_output=True
            )

        except subprocess.CalledProcessError as e:
            print("=== FULL ERROR ===")
            print(f"Return code: {e.returncode}")
            print(f"Command: {e.cmd}")
            print("=== STDOUT ===")
            print(e.stdout)
            print("=== STDERR ===")
            print(e.stderr)
            print("==================")
            log_error(f'Failed to generate syzkaller config: {str(e)[:200]}')  # Truncate log_error
            return None
        
        if not os.path.exists(_CONFIG_PATH):
            log_error('Failed to generate syzkaller config file.')
            return None

        log_success(f'Successfully generated syzkaller config at {_CONFIG_PATH}')

        return KConfig(_CONFIG_PATH)
