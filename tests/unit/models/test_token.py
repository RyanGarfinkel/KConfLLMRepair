from src.models.token import LLMUsage, EmbeddingUsage
from unittest.mock import MagicMock

# Token counts summed across AI messages in response: Success
def test_from_response_with_ai_messages():
	msg = MagicMock()
	msg.type = 'ai'
	msg.usage_metadata = {'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15}
	response = {'messages': [msg]}
	result = LLMUsage.from_response(response)
	assert result.input_tokens == 10
	assert result.output_tokens == 5
	assert result.total_tokens == 15

# Token counts parsed from message with valid metadata: Success
def test_from_ai_message():
	msg = MagicMock()
	msg.usage_metadata = {'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15}
	result = LLMUsage.from_ai_message(msg)
	assert result.input_tokens == 10
	assert result.output_tokens == 5
	assert result.total_tokens == 15

# Token counts default to zero when message metadata is None: Success
def test_from_ai_message_none_metadata():
	msg = MagicMock()
	msg.usage_metadata = None
	result = LLMUsage.from_ai_message(msg)
	assert result.input_tokens == 0
	assert result.output_tokens == 0
	assert result.total_tokens == 0

# Token counts summed when two usages added: Success
def test_llm_usage_addition():
	a = LLMUsage(input_tokens=10, output_tokens=5, total_tokens=15)
	b = LLMUsage(input_tokens=20, output_tokens=10, total_tokens=30)
	result = a + b
	assert result.input_tokens == 30
	assert result.output_tokens == 15
	assert result.total_tokens == 45

# LLMUsage serializes all token fields to dict: Success
def test_llm_usage_model_dump():
	usage = LLMUsage(input_tokens=10, output_tokens=5, total_tokens=15)
	result = usage.model_dump()
	assert result == {'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15}

# Total tokens is sum of build and boot log tokens: Success
def test_embedding_usage_total_tokens():
	usage = EmbeddingUsage(build_log_tokens=30, boot_log_tokens=20)
	assert usage.total_tokens == 50

# EmbeddingUsage serializes token fields with computed total: Success
def test_embedding_usage_model_dump():
	usage = EmbeddingUsage(build_log_tokens=30, boot_log_tokens=20)
	result = usage.model_dump()
	assert result == {'build_log_tokens': 30, 'boot_log_tokens': 20, 'total_tokens': 50}
