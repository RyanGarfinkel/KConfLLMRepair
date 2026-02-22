from pydantic import BaseModel, Field
from typing import Literal

class VerifyResult(BaseModel):

    status: Literal['NOT_STARTED', 'COMPLETED'] = Field(default='NOT_STARTED')

    klocalizer_succeeded: bool = Field(default=False)
    klocalizer_log: str | None = Field(default=None)

    build_succeeded: bool = Field(default=False)
    build_log: str | None = Field(default=None)

    boot_status: Literal['yes', 'maintenance', 'no'] = Field(default='no')
    boot_log: str | None = Field(default=None)

    def model_dump(self) -> dict:
        return {
            'status': self.status,
            'klocalizer_succeeded': self.klocalizer_succeeded,
            'klocalizer_log': self.klocalizer_log,
            'build_succeeded': self.build_succeeded,
            'build_log': self.build_log,
            'boot_status': self.boot_status,
            'boot_log': self.boot_log,
        }
