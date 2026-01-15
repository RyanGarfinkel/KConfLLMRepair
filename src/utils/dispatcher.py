from concurrent.futures import ThreadPoolExecutor, as_completed
from singleton_decorator import singleton
from src.config import settings
from .logger import log
from tqdm import tqdm

@singleton
class Dispatcher:

    def run_tasks(self, tasks: list[callable], handle_as_completed: callable):

        with ThreadPoolExecutor(max_workers=settings.runtime.MAX_THREADS) as executor:

            futures = { executor.submit(task): task for task in tasks }

            for future in tqdm(as_completed(futures), total=len(futures), desc='Running tasks'):
                try:
                    result = future.result()
                    handle_as_completed(result)
                except Exception as e:
                    log.error(f'Task {futures[future]} failed with error: {e}')

dispatcher = Dispatcher()
