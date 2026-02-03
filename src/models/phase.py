from pydantic import BaseModel, Field
from typing import List, Literal
from .token import TokenUsage

class ToolAction(BaseModel):

    name: str = Field(..., frozen=True)
    args: dict = Field(..., frozen=True)
    response: str = Field(..., frozen=True)

class VerifyAction(BaseModel):

    build_succeeded: bool = Field(..., frozen=True)
    build_log: str | None = Field(..., frozen=True)

    boot_succeeded: bool = Field(..., frozen=True)
    boot_log: str | None = Field(..., frozen=True)

class Phase(BaseModel):

    name: Literal['verify', 'analyze', 'collect'] = Field(...)
    actions: List[ToolAction | VerifyAction] = Field(default_factory=list)
    token_usage: TokenUsage = Field(default=TokenUsage(
        input_tokens=0,
        output_tokens=0,
        total_tokens=0
    ))

    def add_tool_action(self, name: str, args: dict, response: str):
        self.actions.append(ToolAction(
            name=name,
            args=args,
            response=response
        ))

    def add_verify_action(self, build_succeeded: bool, build_log: str | None, boot_succeeded: bool, boot_log: str | None):
        self.actions.append(VerifyAction(
            build_succeeded=build_succeeded,
            build_log=build_log,
            boot_succeeded=boot_succeeded,
            boot_log=boot_log
        ))

    def add_token_usage(self, input_tokens: int, output_tokens: int):
        self.token_usage = TokenUsage(
            input_tokens=self.token_usage.input_tokens + input_tokens,
            output_tokens=self.token_usage.output_tokens + output_tokens,
            total_tokens=self.token_usage.total_tokens + input_tokens + output_tokens
        )
