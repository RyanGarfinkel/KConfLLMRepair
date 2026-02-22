from pydantic import BaseModel, Field

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
