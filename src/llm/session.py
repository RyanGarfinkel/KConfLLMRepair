from src.models import Phase, TokenUsage, State
from pydantic import BaseModel, Field
from typing import List, Literal
from src.tools import diffconfig
from src.config import settings

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

    @property
    def num_attempts(self) -> int:
        return len([phase for phase in self.phases if phase.name == 'verify']) - 1

    def model_dump(self, state: State) -> dict:

        if state.get('verify_succeeded', False):
            status = 'succeeded'
        elif state.get('verify_attempts', 0) > settings.agent.MAX_VERIFY_ATTEMPTS:
            status = 'failed'
        elif state.get('tool_calls', 0) > settings.agent.MAX_TOOL_CALLS:
            status = 'max-tool-calls-exceeded'
        else:
            status = 'in-progress'

        if status == 'succeeded':
            diff, edit_distance = diffconfig.compare(state.get('base_config'), state.get('modified_config'))
        else:
            diff = []
            edit_distance = -1

        return {
            'summary': {
                'status': status,
                'num_attempts': self.num_attempts,
                'edit_distance': edit_distance
            },
            'token_usage': self.token_usage.model_dump(),
            'phases': [phase.model_dump() for phase in self.phases],
            'edits': diff,
        }
