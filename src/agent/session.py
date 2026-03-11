
from src.models import Attempt, LLMUsage, EmbeddingUsage
from src.tools import diffconfig
from src.utils import file_lock
from src.config import settings
from typing import Tuple
import time
import json

class Session:
    
    def __init__(self, config: str, output: str, patch: str | None = None):

        self.base = config
        self.attempts: list[Attempt] = []
        self.dir = output
        self.patch = patch
        self.__start_time = time.time()
        self.end_time: float | None = None

    @property
    def duration(self) -> float:
        end = self.end_time if self.end_time is not None else time.time()
        return round(end - self.__start_time, 2)

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
        
        any_maintenance = any(a.boot_succeeded == 'maintenance' for a in self.attempts)
        
        if self.attempts[-1].boot_succeeded == 'yes':
            return 'success'
        elif any_maintenance and attempts >= settings.agent.MAX_ITERATIONS:
            return 'success-maintenance'
        elif attempts >= settings.agent.MAX_ITERATIONS:
            return 'max-attempts-reached'
        
        return 'in-progress'
    
    @property
    def token_usage(self) -> LLMUsage:
        return LLMUsage(
            input_tokens=sum(a.token_usage.input_tokens for a in self.attempts),
            output_tokens=sum(a.token_usage.output_tokens for a in self.attempts),
            total_tokens=sum(a.token_usage.total_tokens for a in self.attempts),
        )

    @property
    def embedding_usage(self) -> EmbeddingUsage:
        return EmbeddingUsage(
            build_log_tokens=sum(a.embedding_usage.build_log_tokens for a in self.attempts),
            boot_log_tokens=sum(a.embedding_usage.boot_log_tokens for a in self.attempts),
        )

    @property
    def constraints(self) -> dict:
        if self.status == 'success':
            attempt = next((a for a in reversed(self.attempts) if a.boot_succeeded == 'yes'), None)
        elif self.status == 'success-maintenance':
            attempt = next((a for a in reversed(self.attempts) if a.boot_succeeded == 'maintenance'), None)
        else:
            return {'defines': 0, 'undefines': 0, 'total': 0}

        if not attempt or not attempt.response:
            return {'defines': 0, 'undefines': 0, 'total': 0}

        defines = len(attempt.response.define)
        undefines = len(attempt.response.undefine)
        return {'defines': defines, 'undefines': undefines, 'total': defines + undefines}

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

        edits, edit_distance = self.edits

        return {
            'summary': {
                'status': self.status,
                'arch': settings.kernel.ARCH,
                'attempts': len(self.attempts) - 1,
                'duration': self.duration,
                'original_config': self.base,
                'repaired_config': repaired_config,
                'edit_distance': edit_distance,
                'total_constraints': self.constraints['total'],
            },
            'models': {
                'llm': settings.agent.MODEL,
                'embedding': settings.agent.EMBEDDING_MODEL if settings.runtime.USE_RAG else None,
            },
            'constraints': self.constraints,
            'llm_token_usage': self.token_usage.model_dump(),
            'embedding_token_usage': self.embedding_usage.model_dump(),
            'attempts': [attempt.model_dump() for attempt in self.attempts],
            'edits': edits
        }
