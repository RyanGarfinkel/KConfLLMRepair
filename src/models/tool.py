from pydantic import BaseModel, Field
from .token import EmbeddingUsage

class ToolCall(BaseModel):
    name: str = Field(..., frozen=True)
    args: dict = Field(..., frozen=True)
    response: str | list[str] | dict = Field(..., frozen=True)
    token_usage: EmbeddingUsage = Field(default_factory=EmbeddingUsage)

    def model_dump(self) -> dict:
        return {
            'name': self.name,
            'args': self.args,
            'response': self.response,
            'token_usage': self.token_usage.model_dump(),
        }
