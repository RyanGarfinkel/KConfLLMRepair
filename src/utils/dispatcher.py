from concurrent.futures import ThreadPoolExecutor, as_completed
from singleton_decorator import singleton
from typing import Callable
from .logger import log
from tqdm import tqdm
import traceback

@singleton
class Dispatcher:

    def run_callables(self, tasks: list[Callable], desc: str = 'Running tasks', labels: list[str] | None = None):

        from src.config import settings
        n = len(tasks)
        max_workers = settings.runtime.MAX_THREADS
        active: set[str] = set()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            pending = {}
            task_iter = iter(enumerate(tasks))

            def submit_next():
                item = next(task_iter, None)
                if item is None:
                    return
                i, task = item
                if labels:
                    active.add(labels[i])
                    pbar.set_postfix_str(', '.join(sorted(active)))
                future = executor.submit(task)
                pending[future] = i

            with tqdm(total=n, desc=desc) as pbar:
                for _ in range(min(max_workers, n)):
                    submit_next()

                while pending:
                    for future in as_completed(pending):
                        i = pending.pop(future)
                        if labels:
                            active.discard(labels[i])
                        try:
                            future.result()
                        except Exception as e:
                            log.error(f'Task failed with error: {e}')
                            log.error(f'Traceback:\n{"".join(traceback.format_exception(type(e), e, e.__traceback__))}')

                        pbar.update(1)
                        pbar.set_postfix_str(', '.join(sorted(active)) if active else '')
                        submit_next()
                        break

dispatcher = Dispatcher()
