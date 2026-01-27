from dataclasses import dataclass, field
from src.models import IterationSummary
from typing import List, Literal
from src.config import settings
import json

@dataclass
class AgentResult:

    provider: str
    model: str
    
    status: Literal['success', 'failure', 'max_iterations']
    iterations: int

    config: str
    input_tokens: int
    output_tokens: int
    total_tokens: int

    history: List[IterationSummary] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'provider': self.provider,
            'model': self.model,
            'status': self.status,
            'iterations': self.iterations,
            'config': self.config,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.total_tokens,
            'history': [iteration.to_dict() for iteration in self.history],
        }
    
    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
    
    @staticmethod
    def save_results(results: List['AgentResult'], path: str):
        
        data = []
        for result in results:
            data.append(result.to_dict())

        summary = {
            'total_samples': len(results),
            'successful': sum(1 for r in results if r.status == 'success'),
            'max_iterations': sum(1 for r in results if r.status == 'max_iterations'),
            'failed': sum(1 for r in results if r.status == 'failure'),
            'results': data,
        }

        with open(path, 'w') as f:
            json.dump(summary, f, indent=4)
