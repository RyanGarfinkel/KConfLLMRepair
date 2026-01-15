from dataclasses import dataclass, field
from src.models import IterationSummary
from typing import List, Literal
from src.config import settings
import json

@dataclass
class AgentResult:

    sample: str

    status: Literal['success', 'failure', 'max_iterations']
    iterations: int

    config: str
    token_usage: int

    history: List[IterationSummary] = field(default_factory=list)
    
    @staticmethod
    def save_results(results: List['AgentResult']):
        
        data = []
        for result in results:
            data.append({
                'sample': result.sample,
                'status': result.status,
                'iterations': result.iterations,
                'config': result.config,
                'token_usage': result.token_usage,
                'history': [iteration.to_dict() for iteration in result.history],
            })

        summary = {
            'total_samples': len(results),
            'successful': sum(1 for r in results if r.status == 'success'),
            'failed': sum(1 for r in results if r.status == 'failure'),
            'results': data,
        }

        with open(f'{settings.runtime.EXPERIMENT_DIR}/summary.json', 'w') as f:
            json.dump(summary, f, indent=4)
