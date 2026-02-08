from concurrent.futures import ThreadPoolExecutor, as_completed
from singleton_decorator import singleton
from src.config import settings
from .logger import log
from tqdm import tqdm
import traceback

@singleton
class Dispatcher:

    def run_tasks(self, tasks: list[callable], desc: str = 'Running tasks'):

        n = len(tasks)
        with ThreadPoolExecutor(max_workers=settings.runtime.MAX_THREADS) as executor:

            futures = { executor.submit(task): task for task in tasks }

            with tqdm(total=n, desc=desc) as pbar:
                for i, future in enumerate(as_completed(futures), start=1):
                    try:
                        future.result()
                    except Exception as e:
                        log.error(f'Task {futures[future]} failed with error: {e}')
                        log.error(f'Traceback:\n{"".join(traceback.format_exception(type(e), e, e.__traceback__))}')

                    pbar.set_description(f'{desc} {i} / {n}')
                    pbar.update(1)

dispatcher = Dispatcher()
