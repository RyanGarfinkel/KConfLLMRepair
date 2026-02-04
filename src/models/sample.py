from dataclasses import dataclass
from src.config import settings
import json
import os

@dataclass
class Sample:
    
    base: str
    modified: str
    patch: str
    kernel_src: str
    output: str
    start_commit: str | None
    end_commit: str | None

    @staticmethod
    def get_samples(n: int) -> list['Sample']:
        
        with open(f'{settings.runtime.SAMPLE_DIR}/info.json') as f:
            data = json.load(f)

        samples = []
        for i, sample_data in enumerate(data['samples']):

            if i >= n:
                break

            if not sample_data['isBaseBootable']:
                continue

            dir = sample_data['dir']

            base = f'{dir}/base.config'
            modified = f'{dir}/modified.config'
            patch = f'{dir}/changes.patch'
            kernel_src = ''
            output = dir
            start_commit = sample_data.get('start_commit', None)
            end_commit = sample_data['end_commit']

            sample = Sample(
                base=base,
                modified=modified,
                patch=patch,
                kernel_src=kernel_src,
                output=output,
                start_commit=start_commit,
                end_commit=end_commit
            )

            samples.append(sample)
        
        return samples

@dataclass
class SampleRaw:

    end_commit: str
    start_commit: str
    commit_date: str
    commit_window: int
    dir: str
    isBaseBootable: bool = False

    def to_dict(self) -> dict:
        return {
            'end_commit': self.end_commit,
            'start_commit': self.start_commit,
            'end_commit_date': self.commit_date,
            'commit_window': self.commit_window,
            'dir': self.dir,
            'isBaseBootable': self.isBaseBootable,
        }

    @staticmethod
    def save_all(sampling_params: dict, samples: list['SampleRaw'], path: str):

        payload = {
            'sampling_parameters': sampling_params,
            'samples': [sample.to_dict() for sample in samples],
        }

        with open(path, 'w') as f:
            json.dump(payload, f, indent=4)
