from dotenv import load_dotenv
from git import Repo
import os

load_dotenv()

# Kernel
kernel_src = '/home/dev/opt/kernel'
kernel_repo = Repo(kernel_src)

# SuperC
superc_linux_script_path = '/home/dev/.local/bin/superc_linux.sh'
# QEMU
debian_img_path = '/home/dev/opt/debian.raw'

qemu_log_dir = '/workspace/logs/qemu'
# os.makedirs(qemu_log_dir, exist_ok=True)

# Syzkaller
syzkaller_yml_path = '/home/dev/opt/syzkaller/dashboard/config/linux/main.yml'
if not os.path.exists(syzkaller_yml_path):
    raise FileNotFoundError(f'Syzkaller config file not found at {syzkaller_yml_path}')

syzkaller_output_path = '/home/dev/opt/syzkaller/dashboard/config/linux/upstream-apparmor-kasan.config'

# Data
patches_dir = '/workspace/data/patches'

base_config_dir = '/workspace/data/base_configs'

klocalizer_config_dir = '/workspace/data/klocalizer_configs'

delta_config_dir = '/workspace/data/delta_configs'

llm_config_dir = '/workspace/data/llm_configs'
