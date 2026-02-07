from langchain_core.messages import HumanMessage
from src.models import State
from src.core import Kernel
import os

class VerifyNode:

    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    def __call__(self, state: State) -> dict:

        verify_attempts = state.get('verify_attempts', 0)
        attempt_dir = f'{state.get('output_dir')}/attempt_{verify_attempts}'
        os.makedirs(attempt_dir, exist_ok=True)

        if not self.kernel.load_config(state.get('modified_config')):
            return {
                'messages': [HumanMessage(content='ERROR: The modified configuration failed to load.')],
                'verify_attempts': verify_attempts + 1,
                'klocalizer_runs': 0,
                'build_log': '',
                'boot_log': '',
                'output_dir': state.get('output_dir'),
                'modified_config': state.get('modified_config'),
            }
        
        if not self.kernel.build(f'{attempt_dir}/build.log'):
            return {
                'messages': [HumanMessage(content='ERROR: Build failed.')],
                'verify_attempts': verify_attempts + 1,
                'klocalizer_runs': 0,
                'build_log': f'{attempt_dir}/build.log',
                'boot_log': '',
                'output_dir': state.get('output_dir'),
                'modified_config': state.get('modified_config'),
            }
        
        if not self.kernel.boot(f'{attempt_dir}/boot.log'):
            return {
                'messages': [HumanMessage(content='ERROR: Boot failed.')],
                'verify_attempts': verify_attempts + 1,
                'klocalizer_runs': 0,
                'build_log': f'{attempt_dir}/build.log',
                'boot_log': f'{attempt_dir}/boot.log',
                'output_dir': state.get('output_dir'),
                'modified_config': state.get('modified_config'),
            }
        
        return {
            'messages': [HumanMessage(content='SUCCESS: The kernel booted on QEMU!')],
            'verify_attempts': verify_attempts + 1,
            'klocalizer_runs': 0,
            'verify_succeeded': True,
            'build_log': f'{attempt_dir}/build.log',
            'boot_log': f'{attempt_dir}/boot.log',
            'output_dir': state.get('output_dir'),
            'modified_config': state.get('modified_config'),
        }
