
from src.models import Attempt, LLMUsage, EmbeddingUsage
from src.kernel import diffconfig
from src.config import settings
from typing import Tuple
import json

class Session:
    
    def __init__(self, config: str, output: str, patch: str | None = None, hard_define: set[str] = set(), hard_undefine: set[str] = set()):

        self.base = config
        self.attempts: list[Attempt] = []
        self.dir = output
        self.patch = patch
        self.hard_define = hard_define
        self.hard_undefine = hard_undefine

    @property
    def latest(self) -> str | None:
        if len(self.attempts) == 0:
            return self.base
        
        return self.attempts[-1].config
    
    @property
    def best_attempt(self) -> Attempt | None:

        if len(self.attempts) == 0:
            return None

        tracking = self.patch is not None and settings.runtime.MIN_COVERAGE > 0

        def rank(a: Attempt) -> float:
            return a.coverage if a.coverage is not None else -1.0

        booted = [a for a in self.attempts if a.boot_succeeded == 'yes']
        if booted:
            return max(booted, key=rank) if tracking else booted[-1]

        maintenance = [a for a in self.attempts if a.boot_succeeded == 'maintenance']
        if maintenance:
            return max(maintenance, key=rank) if tracking else maintenance[-1]

        return self.attempts[-1]

    @property
    def status(self) -> str:

        best = self.best_attempt

        if best is None:
            return 'initialized'

        repair_attempts = len(self.attempts) - 1

        if best.boot_succeeded == 'yes':
            return 'success'
        if best.boot_succeeded == 'maintenance' and repair_attempts >= settings.agent.MAX_ITERATIONS:
            return 'success-maintenance'
        if repair_attempts >= settings.agent.MAX_ITERATIONS:
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
    def total_llm_time(self) -> float:
        return sum(a.llm_time for a in self.attempts)

    @property
    def total_build_time(self) -> float:
        return sum(a.build_time for a in self.attempts)

    @property
    def total_boot_time(self) -> float:
        return sum(a.boot_time for a in self.attempts)

    @property
    def embedding_usage(self) -> EmbeddingUsage:
        return EmbeddingUsage(
            build_log_tokens=sum(a.embedding_usage.build_log_tokens for a in self.attempts),
            boot_log_tokens=sum(a.embedding_usage.boot_log_tokens for a in self.attempts),
        )

    @property
    def constraints(self) -> dict:
        
        best = self.best_attempt
        if self.status not in ('success', 'success-maintenance') or best is None or not best.response:
            return {'defines': 0, 'undefines': 0, 'total': 0}

        defines = len(best.response.define)
        undefines = len(best.response.undefine)
        return {'defines': defines, 'undefines': undefines, 'total': defines + undefines}

    @property
    def edits(self) -> Tuple[list[str], int] | None:
        best = self.best_attempt
        if self.status not in ('success', 'success-maintenance') or best is None or not best.config:
            return [], -1

        return diffconfig.compare(self.base, best.config)
    
    def save(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__(), f, indent=4)
    
    def __dict__(self) -> dict:

        best = self.best_attempt
        repaired_config = best.config if best is not None and self.status in ('success', 'success-maintenance') else None

        edits, edit_distance = self.edits

        summary = {
            'status': self.status,
            'arch': settings.kernel.ARCH,
            'attempts': len(self.attempts) - 1,
            'original_config': self.base,
            'repaired_config': repaired_config,
            'edit_distance': edit_distance,
            'total_constraints': self.constraints['total'],
            'total_llm_time': self.total_llm_time,
            'total_build_time': self.total_build_time,
            'total_boot_time': self.total_boot_time,
        }

        if self.patch is not None:
            summary['patch'] = self.patch
            summary['min_coverage'] = settings.runtime.MIN_COVERAGE
            summary['initial_coverage'] = self.attempts[0].coverage if self.attempts else None
            summary['repaired_coverage'] = best.coverage if best is not None else None

        return {
            'summary': summary,
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
