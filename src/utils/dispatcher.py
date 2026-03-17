from singleton_decorator import singleton
from .logger import log
from tqdm import tqdm
import subprocess
import time
import os

@singleton
class Dispatcher:

    def __init__(self):
        self.log_path: callable | None = None

    def run_tasks(self, commands: list[list[str]], desc: str = 'Running tasks'):

        from src.config import settings

        n = len(commands)
        max_workers = settings.runtime.MAX_THREADS
        command_iter = enumerate(commands)
        pending: dict[subprocess.Popen, list[str]] = {}
        open_files: dict[subprocess.Popen, object] = {}
        completed = 0

        def submit_next():
            entry = next(command_iter, None)
            if entry is None:
                return
            i, cmd = entry
            if self.log_path:
                path = self.log_path(i)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                f = open(path, 'w')
                proc = subprocess.Popen(cmd, stdout=f, stderr=f)
                open_files[proc] = f
            else:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pending[proc] = cmd

        with tqdm(total=n, desc=desc) as pbar:
            for _ in range(min(max_workers, n)):
                submit_next()

            while pending:
                for proc in list(pending):
                    if proc.poll() is not None:
                        pending.pop(proc)
                        if proc in open_files:
                            open_files.pop(proc).close()
                        if proc.returncode != 0:
                            log.error(f'Task failed with code {proc.returncode}: {cmd}')
                        completed += 1
                        pbar.set_description(f'{desc} {completed} / {n}')
                        pbar.update(1)
                        submit_next()
                time.sleep(0.5)

dispatcher = Dispatcher()
