from dotenv import load_dotenv
from git import Repo
import os

load_dotenv()

# SuperC
superc_linux_script_path = '/home/dev/.local/bin/superc_linux.sh'


# Kernel
kernel_src = os.path.expandvars('$KERNEL_SRC')
if not os.path.exists(kernel_src):
    raise FileNotFoundError(f'Kernel source path not found at {kernel_src}')

kernel_repo = Repo(kernel_src)

# QEMU
debian_img_path = '/home/dev/opt/debian.raw'

qemu_log_dir = '/workspace/logs/qemu'
# os.makedirs(qemu_log_dir, exist_ok=True)

# Syzkaller
syzkaller_yml_path = '/home/dev/opt/syzkaller/dashboard/config/linux/main.yml'
# if not os.path.exists(syzkaller_yml_path):
#     raise FileNotFoundError(f'Syzkaller config file not found at {syzkaller_yml_path}')

syzkaller_output_path = '/home/dev/opt/syzkaller/dashboard/config/linux/upstream-apparmor-kasan.config'

from pydantic import field_validator, ValidationError
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):

    ARCH: str
    
    KERNEL_SRC: str
    BZIMAGE_PATH: str = 'arch/x86/boot/bzImage'
    
    SUPERC_PATH: str
    QEMU_TEST_SCRIPT: str

    BASE_DIR: str
    BASE_CONFIG: str
    # SAMPLE_DIR: str
    # EXPERIMENT_DIR: str

    WORKSPACE: str = str(Path(__file__).parent.parent.absolute())

    @classmethod
    @field_validator('KERNEL_SRC', 'SUPERC_PATH', 'QEMU_TEST_SCRIPT')
    def validate_path_exists(cls, v):

        path = v.expanduser().resolve()

        if not path.exists():
            raise ValidationError(f'{path} does not exist.')

        return path

config = Settings()