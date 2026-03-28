from pydantic import BaseModel, Field, field_validator, computed_field, model_validator
from functools import cached_property
import os

class Input(BaseModel):

	original_config: str = Field(..., frozen=True)
	modified_config: str | None = Field(default=None, frozen=True)
	patch: str | None = Field(default=None, frozen=True)
	hard_constraints: str | None = Field(default=None, frozen=True)

	@field_validator('original_config', 'modified_config', 'patch')
	@classmethod
	def validate_file_exists(cls, v: str | None) -> str | None:
		if v is not None and not os.path.exists(v):
			raise ValueError(f'File {v} does not exist.')
		
		return os.path.abspath(v) if v is not None else None

	@field_validator('hard_constraints')
	@classmethod
	def validate_constraints_exists(cls, v: str | None) -> str | None:
		if v is not None and not os.path.exists(v):
			raise ValueError(f'Constraints file {v} does not exist.')
		
		return os.path.abspath(v) if v is not None else None

	@model_validator(mode='after')
	def validate_mode(self):
		if (self.modified_config is None) != (self.patch is None):
			raise ValueError('--modified and --patch must be provided together.')
		
		return self

	@computed_field
	@cached_property
	def define(self) -> set[str]:
		if self.hard_constraints is None:
			return set()

		result = set()
		with open(self.hard_constraints) as f:
			for line in f:
				line = line.strip()
				if line and not line.startswith('!'):
					result.add(line)

		return result

	@computed_field
	@cached_property
	def undefine(self) -> set[str]:
		if self.hard_constraints is None:
			return set()

		result = set()
		with open(self.hard_constraints) as f:
			for line in f:
				line = line.strip()
				if line and line.startswith('!'):
					result.add(line[1:])
		
		return result
