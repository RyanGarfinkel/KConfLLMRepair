import sys
sys.path.insert(0, '/workspace')

from src.core.pipeline import generate_single_baseline
from src.utils.log import log_info
import pandas as pd
import os

sample_size = 1 # 50

cols = ['commit_start', 'commit_end', 'patch_path',
        'base_config', 'base_booted', 'base_qemu_log',
        'klocalizer_config', 'klocalizer_booted', 'klocalizer_qemu_log']
data = []

baseline_dir = '/workspace/data/baselines'
os.makedirs(baseline_dir, exist_ok=True)

for i in range(sample_size):

    log_info(f'Generating sample {i + 1}/{sample_size}...')

    sample_dir = f'{baseline_dir}/sample_{i}'
    os.makedirs(sample_dir, exist_ok=True)

    result = generate_single_baseline(sample_dir)
    while len(result) < len(cols):
        result.append(None)

    data.append(result)

df = pd.DataFrame(data, columns=cols)
df.to_csv(f'{baseline_dir}/summary.csv', index=False)

log_info('Results saved to summary.csv')

base_booted_count = df['base_booted'].sum()
klocalizer_booted_count = df['klocalizer_booted'].sum()
log_info(f'Base configs booted successfully: {base_booted_count}/{sample_size}')
log_info(f'KLocalizer configs booted successfully: {klocalizer_booted_count}/{sample_size}')