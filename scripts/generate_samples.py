import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.pipeline import generate_sample
from src.models.sample import Sample
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

def generate_samples(n):

    dir = f'{WORKSPACE}/data/base/samples'
    os.makedirs(dir, exist_ok=True)

    commit = kernel_repo.head.commit

    csv_path = f'{WORKSPACE}/data/base/samples.csv'
    results = []

    for i in range(n):

        log_info(f'Generating sample {i + 1}/{n}...')

        sample_dir = f'{dir}/sample_{i}'
        os.makedirs(sample_dir, exist_ok=True)

        result = generate_sample(sample_dir, commit)
        commit = kernel_repo.commit(result.start_commit)
        results.append(result)

        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)

    log_info('Finished generating samples.')
    log_info(f'Samples saved to {csv_path}')

    print(df)

@click.command()
@click.option('--n', default=10, help='Number of samples to generate')
def main(n):
    generate_samples(n)

if __name__ == '__main__':
    main()