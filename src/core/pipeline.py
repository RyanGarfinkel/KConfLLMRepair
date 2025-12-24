from time import time
from src.utils.kconfig import apply_llm_suggestions, calculate_delta, chunk_delta
from src.tools.klocalizer import repair as klocalizer_repair
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config import kernel_repo, kernel_src
from src.kernel.builder import make_defconfig
from src.kernel.patches import fetch_patch
from src.llm.client import get_suggestions
import json
import os

def aggregate_suggestions(delta_chunks):

    print('Obtaining LLM suggestions for all delta chunks...')

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {executor.submit(get_suggestions, delta): delta for delta in delta_chunks.values()}

        aggregated_suggestions = {}

        for future in as_completed(futures):
            try:
                suggestions = future.result()
                aggregated_suggestions.update(suggestions)
            except Exception as e:
                print(f'Error obtaining suggestions for chunk: {e}')

    print(f'Aggregated suggestions for {len(aggregated_suggestions)} options from LLM.')

    return aggregated_suggestions


def iteration(commit=kernel_repo.head.commit):

    os.chdir(kernel_src)

    patch_path, parent_commit = fetch_patch(commit)
    if patch_path is None:
        print('No patch to process. Exiting iteration.')
        return
    
    base_config = make_defconfig(commit.hexsha)

    # QEMU TEST base config

    
    klocalizer_config = klocalizer_repair(commit.hexsha, patch_path)

    # DO QEMU TEST HERE ON KLOCALIZER CONFIG

    base_config = '/workspace/data/base_configs/9448598b22c50c8a5bb77a9103e2d49f134c9578.config'
    klocalizer_config = '/workspace/data/klocalizer_configs/9448598b22c50c8a5bb77a9103e2d49f134c9578.config'

    delta, _ = calculate_delta(base_config, klocalizer_config)
    delta_chunks = chunk_delta(delta)

    llm_suggestions = aggregate_suggestions(delta_chunks)

    llm_config = apply_llm_suggestions(commit.hexsha, klocalizer_config, llm_suggestions)

    # Test LLM Suggestions

    os.chdir('/workspace')

    return None
