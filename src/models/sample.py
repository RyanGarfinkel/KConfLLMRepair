from dataclasses import dataclass
from src.config import settings
import pandas as pd
import os

@dataclass
class Sample:
    id: str
    dir: str
    start_commit: str
    end_commit: str
    num_commits: int
    patch: str
    config: str = None
    klocalizer_succeeded : bool = False
    klocalizer_log: str = None
    build_log: str = None
    build_succeeded: bool = False
    qemu_succeeded: bool = False
    qemu_log: str = None

    @staticmethod
    def get_samples(n: int) -> list['Sample']:

        if not os.path.exists(f'{settings.SAMPLE_DIR}/summary.csv'):
            raise FileNotFoundError(f'{settings.SAMPLE_DIR}/summary.csv not found')

        df = pd.read_csv(f'{settings.SAMPLE_DIR}/summary.csv')
        df = df.where(pd.notnull(df), None)
        
        samples = df.apply(lambda row: Sample(**row.to_dict()), axis=1).tolist()

        if n > len(samples):
            raise ValueError(f'Requested {n} samples, but only {len(samples)} available.')

        return samples[:n]
