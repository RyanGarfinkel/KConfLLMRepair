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

@singleton
class Syzkaller:

    def __init__(self):
        self._build_path = None
        self._REPO = Repo(_PATH)
        self._CONFIG_PATH = f'{_PATH}/dashboard/config/linux/upstream-apparmor-kasan.config'
        self._KVM_CONFIG = f'{kernel_src}/kernel/configs/kvm_guest.config'

    def _get_version(self, kernel_commit: Commit) -> Commit:

        kernel_commit_date = kernel_commit.committed_datetime

        try:
            commit = next(self._REPO.iter_commits(until=kernel_commit_date))
            return commit
        except StopIteration:
            log_error('Failed to find syzkaller version for given kernel commit.')
            return None
    
    def _merge_with_kvm_config(self):

        log_info('Merging syzkaller config with KVM guest config...')

        cmd = [
            'scripts/kconfig/merge_config.sh',
            '-m',
            self._CONFIG_PATH,
            self._KVM_CONFIG,
        ]

        subprocess.run(cmd, check=True, cwd=kernel_src)

        log_success('Config merged with KVM guest config successfully.')

        return True
    
    def build_for(self, kernel_commit: Commit) -> bool:

        syz_commit = self._get_version(kernel_commit)

        if syz_commit is None:
            return False
        
        log_info(f'Building syzkaller version {syz_commit.hexsha}')

        self._REPO.git.reset('--hard')
        self._REPO.git.clean('-fdx')
        self._REPO.git.checkout(syz_commit.hexsha)

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
            subprocess.run(cmd, cwd=kernel_src, check=True)

        except subprocess.CalledProcessError as e:

            log_error(f'Failed to generate syzkaller config.')
            log_error(f'Command: {e.cmd}')
            log_error(f'Return code: {e.returncode}')
            log_error(f'stdout: {e.stdout}')
            log_error(f'stderr: {e.stderr}')
            log_error(str(e))
            return None
        
        if not os.path.exists(self._CONFIG_PATH):
            log_error('Failed to generate syzkaller config file.')
            return None
        
        log_success(f'Successfully generated syzkaller config.')
        
        self._merge_with_kvm_config()

        dest_path = f'{kernel_src}/.config'

        if not os.path.exists(dest_path):
            log_error(f'Failed to get merge base config.')
            return None

        log_success(f'Successfully generated base config')

        return KConfig(dest_path)
