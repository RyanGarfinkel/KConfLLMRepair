
from src.models import Attempt, TokenUsage, EmbeddingUsage
from src.tools import diffconfig
from src.utils import file_lock
from src.config import settings
from typing import Tuple
import json
class Session:
    
    def __init__(self, config: str, output: str):

        self.base = config
        self.attempts: list[Attempt] = []
        self.dir = output

    @property
    def latest(self) -> str | None:
        if len(self.attempts) == 0:
            return self.base
        
        return self.attempts[-1].config
    
    @property
    def status(self) -> str:

        attempts = len(self.attempts)

        if attempts == 0:
            return 'initialized'
        
        if self.attempts[-1].boot_succeeded == 'yes':
            return 'success'
        elif self.attempts[-1].boot_succeeded == 'maintenance' and attempts >= settings.agent.MAX_ITERATIONS:
            return 'success-maintenance'
        elif attempts >= settings.agent.MAX_ITERATIONS:
            return 'max-attempts-reached'
        
        return 'in-progress'
    
    @property
    def edits(self) -> Tuple[list[str], int] | None:
        if self.status not in ['success', 'success-maintenance'] or not self.latest:
            return [], -1
        
        return diffconfig.compare(self.base, self.latest)
    
    def save(self, path: str):
        with file_lock:
            with open(path, 'w') as f:
                json.dump(self.__dict__(), f, indent=4)
    
    def __dict__(self) -> dict:

        repaired_config = self.latest if self.status == 'success' else None
        maitence_config = next((attempt.config for attempt in reversed(self.attempts) if attempt.boot_succeeded == 'maintenance'), None)
        if repaired_config is None:
            repaired_config = maitence_config

        token_usage = TokenUsage(
            input_tokens=sum(attempt.token_usage.input_tokens for attempt in self.attempts),
            output_tokens=sum(attempt.token_usage.output_tokens for attempt in self.attempts),
            total_tokens=sum(attempt.token_usage.total_tokens for attempt in self.attempts)
        )

        edits, edit_distance = self.edits

        return {
            'summary': {
                'status': self.status,
                'attempts': len(self.attempts) - 1,
                'original_config': self.base,
                'repaired_config': repaired_config,
                'edit_distance': edit_distance
            },
            'token_usage': token_usage.model_dump(),
            'attempts': [attempt.model_dump() for attempt in self.attempts],
            'edits': edits
        }
