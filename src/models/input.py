from pydantic import BaseModel, Field, field_validator, model_validator
import os

class Input(BaseModel):

	original_config: str = Field(..., frozen=True)
	modified_config: str | None = Field(default=None, frozen=True)
	patch: str | None = Field(default=None, frozen=True)

	@field_validator('original_config', 'modified_config', 'patch')
	@classmethod
	def validate_file_exists(cls, v: str | None) -> str | None:
		if v is not None and not os.path.exists(v):
			raise ValueError(f'File {v} does not exist.')
		return os.path.abspath(v) if v is not None else None

	@model_validator(mode='after')
	def validate_mode(self):
		if (self.modified_config is None) != (self.patch is None):
			raise ValueError('--modified and --patch must be provided together.')
		return self
