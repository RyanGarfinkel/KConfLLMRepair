from dataclasses import dataclass
import json
from src.config import settings
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
    def save_samples(samples: list['Sample']) -> None:

        data = [sample.__dict__ for sample in samples]

        summary = {
            'total_samples': len(samples),
            'successful_klocalizer': sum(1 for s in samples if s.klocalizer_succeeded),
            'successful_builds': sum(1 for s in samples if s.build_succeeded),
            'successful_qemu': sum(1 for s in samples if s.qemu_succeeded),
            'commit_window': samples[0].num_commits,
            'samples': data
        }

        with open(f'{settings.SAMPLE_DIR}/summary.json', 'w') as f:
            json.dump(summary, f, indent=4)

    @staticmethod
    def get_samples(n: int) -> list['Sample']:

        if not os.path.exists(f'{settings.SAMPLE_DIR}/summary.json'):
            raise FileNotFoundError(f'{settings.SAMPLE_DIR}/summary.json not found')

        with open(f'{settings.SAMPLE_DIR}/summary.json', 'r') as f:
            data = json.load(f)
            
        samples = [Sample(**item) for item in data.get('samples', [])]

        return samples[:n]
