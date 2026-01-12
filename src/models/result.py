from src.models import IterationSummary
from dataclasses import dataclass, field
from typing import List, Literal

@dataclass
class AgentResult:

    sample: str

    status: Literal['success', 'failure', 'max_iterations']
    iterations: int

    config: str
    token_usage: int

    history: List[IterationSummary] = field(default_factory=list)
    