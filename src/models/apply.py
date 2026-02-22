from pydantic import BaseModel, Field
from .token import TokenUsage
from .tool import ToolCall
from typing import Literal

class ApplyResult(BaseModel):

    status: Literal['NOT_STARTED', 'COMPLETED'] = Field(default='NOT_STARTED')

    define: list[str] = Field(default_factory=list)
    undefine: list[str] = Field(default_factory=list)
    reasoning: str = Field(default='')

    tool_calls: list[ToolCall] = Field(default_factory=list)

    token_usage: TokenUsage = Field(default=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0))

    def model_dump(self) -> dict:
        return {
            'status': self.status,
            'define': self.define,
            'undefine': self.undefine,
            'reasoning': self.reasoning,
            'tool_calls': [call.model_dump() for call in self.tool_calls],
            'token_usage': self.token_usage.model_dump(),
        }

class ApplyAgentResult(BaseModel):
    
    define: list[str] = Field(description='List of configuration options to define for KLocalizer.')
    undefine: list[str] = Field(description='List of configuration options to undefine for KLocalizer.')
    reasoning: str = Field(description='Reasoning behind what options to define and undefine.')
