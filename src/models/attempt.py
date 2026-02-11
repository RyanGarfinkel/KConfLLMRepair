
from pydantic import BaseModel, Field
from .response import AgentResponse

class TokenUsage(BaseModel):
    input_tokens: int = Field(..., frozen=True)
    output_tokens: int = Field(..., frozen=True)
    total_tokens: int = Field(..., frozen=True)

    def model_dump(self) -> dict:
        return {
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.total_tokens,
        }

class ToolCall(BaseModel):
    name: str = Field(..., frozen=True)
    args: dict = Field(..., frozen=True)
    response: str | list[str] | dict = Field(..., frozen=True)

    def model_dump(self) -> dict:
        return {
            'name': self.name,
            'args': self.args,
            'response': self.response
        }

class Attempt(BaseModel):

    id: int = Field(..., frozen=True)

    dir: str = Field(..., frozen=True)

    klocalizer_succeeded: bool = Field(default=False)
    klocalizer_log: str | None = Field(default=None)
    config: str | None = Field(default=None)

    build_succeeded: bool = Field(default=False)
    build_log: str | None = Field(default=None)

    boot_succeeded: bool = Field(default=False)
    boot_log: str | None = Field(default=None)

    tool_calls: list[ToolCall] = Field(default_factory=list)
    response: AgentResponse | None = Field(default=None)
    
    token_usage: TokenUsage = Field(default=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0))

    def add_token_usage(self, input_tokens: int, output_tokens: int, total_tokens: int):
        self.token_usage = TokenUsage(
            input_tokens=self.token_usage.input_tokens + input_tokens,
            output_tokens=self.token_usage.output_tokens + output_tokens,
            total_tokens=self.token_usage.total_tokens + total_tokens
        )

    def model_dump(self) -> dict:
        return {
            'attempt': self.id,
            'summary': {
                'klocalizer_succeeded': self.klocalizer_succeeded,
                'klocalizer_log': self.klocalizer_log,
                'modified_config': self.config,
                'build_succeeded': self.build_succeeded,
                'build_log': self.build_log,
                'boot_succeeded': self.boot_succeeded,
                'boot_log': self.boot_log,
            },
            'token_usage': self.token_usage.model_dump(),
            'tool_calls': [call.model_dump() for call in self.tool_calls],
            'changes': {
                'define': self.response.define if self.response else None,
                'undefine': self.response.undefine if self.response else None,
                'reason': self.response.reasoning if self.response else None,
            }
        }
