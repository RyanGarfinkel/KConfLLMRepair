from pydantic import BaseModel, Field
from typing import Literal

class BuildResult(BaseModel):
	ok: bool = Field(..., frozen=True)
	log: str = Field(..., frozen=True)
	build_time: float = Field(..., ge=0, frozen=True)
	summary: str | None = Field(default=None, frozen=True)

class BootResult(BaseModel):
	status: Literal['yes', 'maintenance', 'panic', 'timeout', 'no'] = Field(..., frozen=True)
	log: str = Field(..., frozen=True)
	boot_time: float = Field(default=0.0, ge=0, frozen=True)
	summary: str | None = Field(default=None, frozen=True)

class KlocalizerResult(BaseModel):
	status: Literal['success', 'no-satisfying-constraints', 'error'] = Field(..., frozen=True)
	log: str = Field(..., frozen=True)
