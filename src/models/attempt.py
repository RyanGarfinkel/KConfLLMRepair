from pydantic import BaseModel, Field
from .analyze import AnalyzeResult
from .verify import VerifyResult
from .apply import ApplyResult
from .token import TokenUsage
from typing import Literal

class Attempt(BaseModel):

    id: int = Field(..., frozen=True)
    dir: str = Field(..., frozen=True)

    @property
    def status(self) -> Literal['IN_PROGRESS', 'BUILD_FAILED', 'BOOT_FAILED', 'BOOT_MAINTENANCE', 'BOOT_SUCCEEDED', 'ERROR']:
        if self.verify.status == 'NOT_STARTED':
            return 'IN_PROGRESS'
        elif not self.verify.build_succeeded:
            return 'BUILD_FAILED'
        elif self.verify.boot_status == 'no':
            return 'BOOT_FAILED'
        elif self.verify.boot_status == 'maintenance':
            return 'BOOT_MAINTENANCE'
        elif self.verify.boot_status == 'yes':
            return 'BOOT_SUCCEEDED'
        else:
            return 'ERROR'

    analyze: AnalyzeResult = Field(default_factory=AnalyzeResult)
    apply: ApplyResult = Field(default_factory=ApplyResult)
    verify: VerifyResult = Field(default_factory=VerifyResult)

    @property
    def token_usage(self) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.analyze.token_usage.input_tokens + self.apply.token_usage.input_tokens,
            output_tokens=self.analyze.token_usage.output_tokens + self.apply.token_usage.output_tokens,
            total_tokens=self.analyze.token_usage.total_tokens + self.apply.token_usage.total_tokens,
        )

    def model_dump(self) -> dict:
        return {
            'attempt': self.id,
            'status': self.status,
            'token_usage': self.token_usage.model_dump(),
            'analyze': self.analyze.model_dump(),
            'apply': self.apply.model_dump(),
            'verify': self.verify.model_dump(),
        }
