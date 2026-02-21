from pydantic import BaseModel, Field

class EmbeddingUsage(BaseModel):

    klocalizer_log_tokens: int = Field(default=0, frozen=True)
    build_log_tokens: int = Field(default=0, frozen=True)
    boot_log_tokens: int = Field(default=0, frozen=True)

    @property
    def total_tokens(self) -> int:
        return self.klocalizer_log_tokens + self.build_log_tokens + self.boot_log_tokens
    
    def model_dump(self) -> dict:
        return {
            'klocalizer_log_tokens': self.klocalizer_log_tokens,
            'build_log_tokens': self.build_log_tokens,
            'boot_log_tokens': self.boot_log_tokens,
            'total_tokens': self.total_tokens,
        }
