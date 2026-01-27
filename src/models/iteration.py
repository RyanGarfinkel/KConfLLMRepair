from pydantic import BaseModel, Field
from dataclasses import dataclass
from typing import Any

@dataclass
class IterationSummary:

    executor_summary: 'ExecutorSummary'
    input_tokens: int
    output_tokens: int
    total_tokens: int
    tools_used: dict
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'executor_summary': self.executor_summary.model_dump(),
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.total_tokens,
            'tools_used': self.tools_used
        }

class ExecutorSummary(BaseModel):

    thoughts: str = Field(
        description='The reasoning behind the actions taken in this iteration.'
    )

    observations: str = Field(
        description='The observations made during this iteration.'
    )

    actions: str = Field(
        description='The actions taken during this iteration.'
    )

    next_steps: str = Field(
        description='The next steps to be taken in the repair process during the next iteration and why.'
    )