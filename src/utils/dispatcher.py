from concurrent.futures import ThreadPoolExecutor, as_completed
from singleton_decorator import singleton
from .logger import log
from tqdm import tqdm
import traceback

@singleton
class Dispatcher:

    def run_tasks(self, tasks: list[callable], desc: str = 'Running tasks'):

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

            with tqdm(total=n, desc=desc) as pbar:
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
                        pbar.set_description(f'{desc} {completed} / {n}')
                        pbar.update(1)
                        submit_next()
                        break

dispatcher = Dispatcher()
