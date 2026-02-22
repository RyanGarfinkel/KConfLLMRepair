from pydantic import BaseModel, Field
from .token import TokenUsage
from .tool import ToolCall
from typing import Literal

class AnalyzeResult(BaseModel):

    status: Literal['NOT_STARTED', 'COMPLETED'] = Field(default='NOT_STARTED')

    hypothesis: str = Field(default='')

    tool_calls: list[ToolCall] = Field(default_factory=list)

    token_usage: TokenUsage = Field(default=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0))

    def model_dump(self) -> dict:
        return {
            'status': self.status,
            'hypothesis': self.hypothesis,
            'tool_calls': [call.model_dump() for call in self.tool_calls],
            'token_usage': self.token_usage.model_dump(),
        }

class AnalyzeAgentResult(BaseModel):

    hypothesis: str = Field(..., frozen=True)
