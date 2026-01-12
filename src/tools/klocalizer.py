from src.kernel import KernelRepo, KConfig
from singleton_decorator import singleton
from src.config import settings
from src.utils import log
import subprocess
import os

@singleton
class KLocalizer:

    def run(self, repo: KernelRepo, output_dir: str, define: list[str] = [], undefine: list[str] = []) -> KConfig | None:
        
        os.makedirs(output_dir, exist_ok=True)

        # Verify patch exists
        patch_path = f'{output_dir}/changes.patch'
        if not os.path.exists(patch_path):
            log.error(f'Patch file {patch_path} does not exist. Cannot run KLocalizer for commit {repo.commit}.')
            return None

        # Run KLocalizer
        log.info(f'Running KLocalizer for commit {repo.commit}...')

        cmd = [
            'klocalizer',
            '--superc-linux-script', settings.SUPERC_PATH,
            '--include-mutex', patch_path,
            '--cross-compiler', 'gcc',
            '--arch', settings.ARCH
        ]

        for opt in define:
            cmd.extend(['--define', opt])
            
        for opt in undefine:
            cmd.extend(['--undefine', opt])

        log_file = f'{output_dir}/klocalizer.log'
        
        try:
            with open(log_file, 'w') as f:
                result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=repo.path, text=True, bufsize=1)

                for line in result.stdout:
                    f.write(line)
                    f.flush()
                
                result.wait()
            
            if result.returncode != 0:
                log.error(f'klocalizer repair failed for commit {repo.commit}. Check log for details.')
                return None
            
            klocalizer_config = KConfig(f'{repo.path}/0-{settings.ARCH}.config')
            klocalizer_config.mv(f'{repo.path}/.config')

            os.remove(f'{output_dir}/changes.patch.kloc_targets')
            
            log.success('klocalizer repair completed.')

            return klocalizer_config
        except subprocess.CalledProcessError as e:
            log.error(f'klocalizer repair failed: {e}')
            return None

klocalizer = KLocalizer()
