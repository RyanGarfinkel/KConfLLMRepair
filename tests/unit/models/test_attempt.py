from src.models.token import LLMUsage, EmbeddingUsage
from src.models.response import AgentResponse
from src.models.attempt import Attempt
from src.models.tool import ToolCall

# Attempt with no changes or tool calls: Success
def test_model_dump_minimal(tmp_path):
	attempt = Attempt(id=0, dir=str(tmp_path))
	result = attempt.model_dump()

	assert result['attempt'] == 0
	assert result['summary']['klocalizer_status'] == 'not-run'
	assert result['summary']['build_succeeded'] is False
	assert result['summary']['boot_succeeded'] == 'no'
	assert result['summary']['tool_call_count'] == 0
	assert result['summary']['total_token_usage'] == 0
	assert result['changes']['define'] is None
	assert result['changes']['undefine'] is None
	assert result['changes']['reason'] is None
	assert result['tool_calls'] == []

# Attempt with response, tool calls, and token usage: Success
def test_model_dump_with_response_and_tool_calls(tmp_path):
	response = AgentResponse(define=['CONFIG_X'], undefine=['CONFIG_Y'], reasoning='test reason')
	tool_call = ToolCall(
		name='grep_build_log',
		args={'pattern': 'error'},
		response='some output',
		token_usage=EmbeddingUsage(build_log_tokens=10, boot_log_tokens=5),
	)
	attempt = Attempt(
		id=1,
		dir=str(tmp_path),
		config=str(tmp_path / 'config'),
		klocalizer_status='success',
		build_succeeded=True,
		boot_succeeded='yes',
		response=response,
		tool_calls=[tool_call],
		token_usage=LLMUsage(input_tokens=100, output_tokens=50, total_tokens=150),
		embedding_usage=EmbeddingUsage(build_log_tokens=20, boot_log_tokens=10),
	)
	result = attempt.model_dump()

	assert result['attempt'] == 1
	assert result['summary']['klocalizer_status'] == 'success'
	assert result['summary']['build_succeeded'] is True
	assert result['summary']['boot_succeeded'] == 'yes'
	assert result['summary']['tool_call_count'] == 1
	assert result['summary']['total_token_usage'] == 150 + 30 + 15
	assert result['changes']['define'] == ['CONFIG_X']
	assert result['changes']['undefine'] == ['CONFIG_Y']
	assert result['changes']['reason'] == 'test reason'
	assert len(result['tool_calls']) == 1
	assert result['tool_calls'][0]['name'] == 'grep_build_log'
