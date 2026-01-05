from src.tools.klocalizer import run_klocalizer
from src.config import base_config_dir, kernel_src, patches_dir
from langchain.tools import tool
import subprocess

def get_agent_tools(commit_hexsha):

    base_config_path = f'{base_config_dir}/{commit_hexsha}.config'
    patch_path = f'{patches_dir}/{commit_hexsha}.patch'

    @tool
    def run_klocalizer(define, undefine):
        """
        Runs the klocalizer tool with the given define and undefine options. The delta
        configuration is updated afterwards.
        Args:
            define list[str]: List of configuration options that the klocalizer tool keeps enabled.
            undefine list[str]: List of configuration option names that the klocalizer tool keeps disabled.

        Returns:
            bool: True if the tool ran successfully, False otherwise.
        """

        base_config_path = f'{base_config_dir}/{commit_hexsha}.config'
        result = subprocess.run(f'cp {base_config_path} {kernel_src}/.config', shell=True, check=True)
        if result.returncode != 0:
            raise Exception('Failed to copy base config file to kernel source directory')
        
        updated_config_path = run_klocalizer(
            commit_hash=commit_hexsha,
            patch_path=patch_path,
            define=define,
            undefine=undefine
        )

        return updated_config_path is not None
    
    return [run_klocalizer]
