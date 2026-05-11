from pydantic import BaseModel, Field

class LLMUsage(BaseModel):
	input_tokens: int = Field(..., frozen=True)
	output_tokens: int = Field(..., frozen=True)
	total_tokens: int = Field(..., frozen=True)

	@classmethod
	def from_response(cls, response: dict) -> 'LLMUsage':
		ai_messages = [msg for msg in response.get('messages', []) if msg.type == 'ai']
		return cls(
			input_tokens=sum(msg.usage_metadata['input_tokens'] for msg in ai_messages if msg.usage_metadata),
			output_tokens=sum(msg.usage_metadata['output_tokens'] for msg in ai_messages if msg.usage_metadata),
			total_tokens=sum(msg.usage_metadata['total_tokens'] for msg in ai_messages if msg.usage_metadata),
		)

	@classmethod
	def from_ai_message(cls, message) -> 'LLMUsage':
		meta = message.usage_metadata or {}
		return cls(
			input_tokens=meta.get('input_tokens', 0),
			output_tokens=meta.get('output_tokens', 0),
			total_tokens=meta.get('total_tokens', 0),
		)

	def __add__(self, other: 'LLMUsage') -> 'LLMUsage':
		return LLMUsage(
			input_tokens=self.input_tokens + other.input_tokens,
			output_tokens=self.output_tokens + other.output_tokens,
			total_tokens=self.total_tokens + other.total_tokens,
		)

	def model_dump(self) -> dict:
		return {
			'input_tokens': self.input_tokens,
			'output_tokens': self.output_tokens,
			'total_tokens': self.total_tokens,
		}

class EmbeddingUsage(BaseModel):
	build_log_tokens: int = Field(default=0, frozen=True)
	boot_log_tokens: int = Field(default=0, frozen=True)

	@property
	def total_tokens(self) -> int:
		return self.build_log_tokens + self.boot_log_tokens

	def model_dump(self) -> dict:
		return {
			'build_log_tokens': self.build_log_tokens,
			'boot_log_tokens': self.boot_log_tokens,
			'total_tokens': self.total_tokens,
		}
