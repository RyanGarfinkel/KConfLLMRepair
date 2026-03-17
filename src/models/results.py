from pydantic import BaseModel
from typing import Literal

class BuildResult(BaseModel):
	ok: bool
	log: str

class BootResult(BaseModel):
	status: Literal['yes', 'maintenance', 'no']
	log: str

class KlocalizerResult(BaseModel):
	status: Literal['success', 'no-satisfying-constraints', 'error']
	log: str
