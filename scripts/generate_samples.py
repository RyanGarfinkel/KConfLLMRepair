import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.pipeline import generate_sample, cols
from src.utils.log import log_info
from dotenv import load_dotenv
from git import Repo
import pandas as pd
import click

load_dotenv()

WORKSPACE = os.getenv('WORKSPACE')
if not WORKSPACE:
    raise EnvironmentError('WORKSPACE environment variable not set.')

kernel_src = os.getenv('KERNEL_SRC')
if not kernel_src:
    raise EnvironmentError('KERNEL_SRC environment variable not set.')

kernel_repo = Repo(kernel_src)

def generate_samples(size):

    dir = f'{WORKSPACE}/data/base/samples'
    os.makedirs(dir, exist_ok=True)

    commit = kernel_repo.head.commit

    for i in range(size):

        log_info(f'Generating sample {i + 1}/{size}...')

        sample_dir = f'{dir}/sample_{i}'
        os.makedirs(sample_dir, exist_ok=True)

        result = generate_sample(sample_dir, commit)
        commit = result[0]
        
        while len(result) < 5:
            result.append(None)

    log_info('Finished generating samples.')

    csv_path = f'{WORKSPACE}/data/base/samples.csv'
    df = pd.DataFrame([result], columns=cols)
    df.to_csv(csv_path, index=False)
    log_info(f'Samples saved to {csv_path}')

    print(df.head())

@click.command()
@click.option('--size', default=1, help='Number of samples to generate')
def main(size):
    generate_samples(size)

if __name__ == '__main__':
    main()