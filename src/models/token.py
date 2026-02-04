from pydantic import BaseModel, Field

class TokenUsage(BaseModel):
    
    input_tokens: int = Field(..., frozen=True, ge=0)
    output_tokens: int = Field(..., frozen=True, ge=0)
    total_tokens: int = Field(..., frozen=True, ge=0)

    def model_dump(self):
        return {
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.total_tokens
        }
