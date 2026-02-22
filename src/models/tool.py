from pydantic import BaseModel, Field

class ToolCall(BaseModel):

    name: str = Field(..., frozen=True)
    args: dict = Field(..., frozen=True)
    response: str | list[str] | dict = Field(..., frozen=True)

    def model_dump(self) -> dict:
        return {
            'name': self.name,
            'args': self.args,
            'response': self.response,
        }
