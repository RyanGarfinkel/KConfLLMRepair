from src.models import Phase, TokenUsage
from pydantic import BaseModel, Field
from typing import List, Literal

class Session(BaseModel):
    
    phases: List[Phase] = Field(default_factory=list)
    @property
    def current_phase(self) -> Phase | None:
        if self.phases:
            return self.phases[-1]
        
        return None
    
    def start_phase(self, name: Literal['verify', 'analyze', 'collect']):
        phase = Phase(name=name)
        self.phases.append(phase)
    
    @property
    def token_usage(self) -> TokenUsage:
        input = sum(phase.token_usage.input_tokens for phase in self.phases)
        output = sum(phase.token_usage.output_tokens for phase in self.phases)

        return TokenUsage(
            input_tokens=input,
            output_tokens=output,
            total_tokens=input + output
        )
    
    output_dir: str = Field(..., frozen=True)
    attempt_dir: str = Field('attempt_0')

    @property
    def num_attempts(self) -> int:
        return len([phase for phase in self.phases if phase.name == 'verify']) - 1
