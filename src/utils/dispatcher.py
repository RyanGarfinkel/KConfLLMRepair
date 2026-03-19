from concurrent.futures import ThreadPoolExecutor, as_completed
from singleton_decorator import singleton
from .logger import log
from tqdm import tqdm
import subprocess
import traceback
import time
import os

@singleton
class Dispatcher:

    def run_repairs(self, commands: list[list[str]], log_path: callable | None = None, on_complete: callable | None = None):

        from src.config import settings

        n = len(commands)
        command_iter = enumerate(commands)
        pending: dict[subprocess.Popen, tuple[int, list[str], float]] = {}
        open_files: dict[subprocess.Popen, object] = {}
        completed = 0

        def submit_next():
            entry = next(command_iter, None)
            if entry is None:
                return
            i, cmd = entry
            start_time = time.time()
            if log_path:
                path = log_path(i)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                f = open(path, 'w')
                proc = subprocess.Popen(cmd, stdout=f, stderr=f)
                open_files[proc] = f
            else:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pending[proc] = (i, cmd, start_time)

        with tqdm(total=n, desc='Running repairs') as pbar:
            for _ in range(min(settings.runtime.MAX_THREADS, n)):
                submit_next()

            while pending:
                for proc in list(pending):
                    if proc.poll() is not None:
                        i, cmd, start_time = pending.pop(proc)
                        duration = round(time.time() - start_time, 2)
                        if proc in open_files:
                            open_files.pop(proc).close()
                        if proc.returncode != 0:
                            log.error(f'Repair failed with code {proc.returncode}: {cmd}')
                        if on_complete:
                            on_complete(i, duration)
                        completed += 1
                        pbar.set_description(f'Running repairs {completed} / {n}')
                        pbar.update(1)
                        submit_next()
                time.sleep(0.5)

    def run_callables(self, tasks: list[callable]):

        from src.config import settings
        n = len(tasks)
        max_workers = settings.runtime.MAX_THREADS

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            pending = {}
            task_iter = iter(tasks)
            completed = 0

            def submit_next():
                task = next(task_iter, None)
                if task is not None:
                    future = executor.submit(task)
                    pending[future] = task

            with tqdm(total=n, desc='Generating samples') as pbar:
                for _ in range(min(max_workers, n)):
                    submit_next()

                while pending:
                    for future in as_completed(pending):
                        task = pending.pop(future)
                        try:
                            future.result()
                        except Exception as e:
                            log.error(f'Task {task} failed with error: {e}')
                            log.error(f'Traceback:\n{"".join(traceback.format_exception(type(e), e, e.__traceback__))}')

                        completed += 1
                        pbar.set_description(f'Generating samples {completed} / {n}')
                        pbar.update(1)
                        submit_next()
                        break

dispatcher = Dispatcher()
