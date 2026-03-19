from pydantic import BaseModel, Field
from typing import Literal

class BuildResult(BaseModel):
	ok: bool = Field(..., frozen=True)
	log: str = Field(..., frozen=True)
	build_time: float = Field(..., ge=0, frozen=True)

class BootResult(BaseModel):
	status: Literal['yes', 'maintenance', 'no'] = Field(..., frozen=True)
	log: str = Field(..., frozen=True)

class KlocalizerResult(BaseModel):
	status: Literal['success', 'no-satisfying-constraints', 'error'] = Field(..., frozen=True)
	log: str = Field(..., frozen=True)
