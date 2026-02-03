from pydantic import BaseModel, Field

class TokenUsage(BaseModel):
    
    input_tokens: int = Field(..., frozen=True, ge=0)
    output_tokens: int = Field(..., frozen=True, ge=0)
    total_tokens: int = Field(..., frozen=True, ge=0)
