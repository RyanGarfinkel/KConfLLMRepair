import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.log import log_info, log_error, log_success
from src.core.pipeline import repair_sample
from src.models.sample import Sample
from dotenv import load_dotenv
import pandas as pd
import click

load_dotenv()

WORKSPACE = os.getenv('WORKSPACE')
if not WORKSPACE:
    raise EnvironmentError('WORKSPACE not set.')

def repair_samples(n):

    dir = f'{WORKSPACE}/data/experiments'
    df = pd.read_csv(f'{WORKSPACE}/data/base/samples.csv')
    samples = df.apply(lambda row: Sample(**row), axis=1).tolist()

    for i in range(n):

        log_info(f'Repairing sample {i + 1}/{n}...')

        sample_dir = f'{dir}/sample_{i}'
        os.makedirs(sample_dir, exist_ok=True)

        # Copy initial sample
        if not os.path.exists(f'{WORKSPACE}/data/base/samples/sample_{i}'):
            log_error(f'Initial sample {i} not found. Skipping.')
            continue

        os.makedirs(f'{sample_dir}/try_0', exist_ok=True)
        os.system(f'cp -r {WORKSPACE}/data/base/samples/sample_{i}/* {sample_dir}/try_0/')

        result = repair_sample(samples[i], sample_dir)

        if result.qemu_boot_result:
            log_success(f'Sample {i} repaired successfully!')
        else:
            log_error(f'Sample {i} repair failed.')

@click.command()
@click.option('--n', default=1, help='Number of samples to repair.')
def main(n):
    repair_samples(n)

if __name__ == '__main__':
    main()
