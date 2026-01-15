from pydantic import BaseModel, Field
from dataclasses import dataclass
from typing import Any

@dataclass
class IterationSummary:

    executor_summary: 'ExecutorSummary'
    token_usage: int
    tools_used: dict
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'executor_summary': self.executor_summary.model_dump(),
            'token_usage': self.token_usage,
            'tools_used': self.tools_used
        }

class ExecutorSummary(BaseModel):

    thoughts: str = Field(
        description='The reasoning behind the actions taken in this iteration.'
    )

    observations: str = Field(
        description='The observations made during this iteration.'
    )

    suggestions: str = Field(
        description='The suggestions for the next steps to take in the repair process.'
    )