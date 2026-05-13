from .token import LLMUsage, EmbeddingUsage
from pydantic import BaseModel, Field
from .response import AgentResponse
from .tool import ToolCall
from typing import Literal

class Attempt(BaseModel):

    id: int = Field(..., frozen=True)

    config: str | None = Field(default=None)
    dir: str = Field(..., frozen=True)

    klocalizer_status: Literal['success', 'no-satisfying-constraints', 'error', 'not-run'] = Field(default='not-run')
    klocalizer_log: str | None = Field(default=None)

    build_succeeded: bool = Field(default=False)
    build_log: str | None = Field(default=None)
    build_time: float = Field(default=0.0, ge=0)

    boot_succeeded: Literal['yes', 'maintenance', 'no'] = Field(default='no')
    boot_log: str | None = Field(default=None)
    boot_time: float = Field(default=0.0, ge=0)

    tool_calls: list[ToolCall] = Field(default_factory=list)
    response: AgentResponse | None = Field(default=None)
    
    embedding_usage: EmbeddingUsage = Field(default_factory=EmbeddingUsage)
    llm_time: float = Field(default=0.0, ge=0)
    token_usage: LLMUsage = Field(default=LLMUsage(input_tokens=0, output_tokens=0, total_tokens=0))

    def model_dump(self) -> dict:
        total_tool_call_tokens = sum(call.token_usage.total_tokens for call in self.tool_calls)
        return {
            'attempt': self.id,
            'summary': {
                'klocalizer_status': self.klocalizer_status,
                'klocalizer_log': self.klocalizer_log,
                'modified_config': self.config,
                'build_succeeded': self.build_succeeded,
                'build_log': self.build_log,
                'build_time': self.build_time,
                'boot_succeeded': self.boot_succeeded,
                'boot_log': self.boot_log,
                'boot_time': self.boot_time,
                'llm_time': self.llm_time,
                'total_token_usage': self.token_usage.total_tokens + self.embedding_usage.total_tokens + total_tool_call_tokens,
            },
            'token_usage': self.token_usage.model_dump(),
            'embedding_usage': self.embedding_usage.model_dump(),
            'tool_calls': [call.model_dump() for call in self.tool_calls],
            'changes': {
                'define': self.response.define if self.response else None,
                'undefine': self.response.undefine if self.response else None,
                'reason': self.response.reasoning if self.response else None,
            }
        }
