from dotenv import load_dotenv
from git import Repo
import os

load_dotenv()

# Kernel
kernel_src = '/workspace/kernel'
kernel_repo = Repo(kernel_src)

# SuperC
superc_linux_script_path = '/usr/local/bin/superc-linux'

# Data
patches_dir = '/workspace/data/patches'
os.makedirs(patches_dir, exist_ok=True)

base_config_dir = '/workspace/data/base_configs'
os.makedirs(base_config_dir, exist_ok=True)

klocalizer_config_dir = '/workspace/data/klocalizer_configs'
os.makedirs(klocalizer_config_dir, exist_ok=True)

delta_config_dir = '/workspace/data/delta_configs'
os.makedirs(delta_config_dir, exist_ok=True)

llm_config_dir = '/workspace/data/llm_configs'
os.makedirs(llm_config_dir, exist_ok=True)
