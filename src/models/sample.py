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
            'commit_date': self.commit_date,
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