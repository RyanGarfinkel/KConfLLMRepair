from src.models import Attempt, AgentResponse, Input
from unittest.mock import patch, MagicMock
from src.agent import agent_tools, prompt
from contextlib import ExitStack
from src.core.agent import agent
from src.config import settings
from src.agent import Session
from src.agent import model
import pytest
import sys

agent_core = sys.modules['src.core.agent']

@pytest.fixture(autouse=True)
def restore_settings():
	saved_output = settings.runtime.OUTPUT_DIR
	saved_iterations = settings.agent.MAX_ITERATIONS
	yield
	settings.runtime.OUTPUT_DIR = saved_output
	settings.agent.MAX_ITERATIONS = saved_iterations

@pytest.fixture
def repair_input(tmp_path):
	p = tmp_path / 'test.config'
	p.touch()

	return Input(original_config=str(p))

@pytest.fixture
def session(tmp_path):
	return Session(config=f'{tmp_path}/base.config', output=str(tmp_path))

def _attempt(id, dir, config=None, boot='no'):
	return Attempt(id=id, dir=str(dir), config=config, boot_succeeded=boot)

def _run_repair(repair_input, initial, side_effect):
	with ExitStack() as stack:
		stack.enter_context(patch.object(agent, '_Agent__make_dir'))
		stack.enter_context(patch.object(agent, '_Agent__inital_attempt', return_value=initial))
		stack.enter_context(patch.object(agent, '_Agent__attempt', side_effect=side_effect))
		stack.enter_context(patch.object(model, 'get_llm', return_value=MagicMock()))
		stack.enter_context(patch.object(Session, 'save'))
		mock_copy = stack.enter_context(patch('shutil.copyfile'))
		agent.repair(repair_input, MagicMock())
		
	return mock_copy

# Repair output: Success
def test_success(repair_input, tmp_path):
	settings.agent.MAX_ITERATIONS = 2
	output_dir = f'{tmp_path}/out'
	settings.runtime.OUTPUT_DIR = output_dir

	repaired_config = f'{tmp_path}/repaired.config'
	initial = _attempt(0, tmp_path)

	def append_success(_, __, session):
		session.attempts.append(_attempt(1, tmp_path, config=repaired_config, boot='yes'))

	mock_copy = _run_repair(repair_input, initial, append_success)
	mock_copy.assert_called_once_with(repaired_config, f'{output_dir}/repaired.config')

# Repair output: Success (maintenance)
def test_success_maintenance(repair_input, tmp_path):
	settings.agent.MAX_ITERATIONS = 2
	output_dir = f'{tmp_path}/out'
	settings.runtime.OUTPUT_DIR = output_dir

	maintenance_config = f'{tmp_path}/maintenance.config'
	initial = _attempt(0, tmp_path)
	call_count = {'n': 0}

	def append_attempts(_, __, session):
		call_count['n'] += 1
		if call_count['n'] == 1:
			session.attempts.append(_attempt(1, tmp_path, config=maintenance_config, boot='maintenance'))
		else:
			session.attempts.append(_attempt(call_count['n'], tmp_path))

	mock_copy = _run_repair(repair_input, initial, append_attempts)
	mock_copy.assert_called_once_with(maintenance_config, f'{output_dir}/repaired.config')

# Repair output: Max attempts
def test_max_attempts(repair_input, tmp_path):
	settings.agent.MAX_ITERATIONS = 2
	output_dir = f'{tmp_path}/out'
	settings.runtime.OUTPUT_DIR = output_dir

	initial = _attempt(0, tmp_path)
	call_count = {'n': 0}

	def append_failed(_, __, session):
		call_count['n'] += 1
		session.attempts.append(_attempt(call_count['n'], tmp_path))

	mock_copy = _run_repair(repair_input, initial, append_failed)
	mock_copy.assert_not_called()

# Wrapper fallback accumulates tokens on top of base usage: Success
def test_generate_response_wrapper_tracks_tokens(session):
	base_msg = MagicMock()
	base_msg.type = 'ai'
	base_msg.usage_metadata = {'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15}

	wrapper_raw = MagicMock()
	wrapper_raw.usage_metadata = {'input_tokens': 20, 'output_tokens': 8, 'total_tokens': 28}

	agent_result = {'messages': [base_msg]}
	wrapper_result = {'raw': wrapper_raw, 'parsed': AgentResponse(define=[], undefine=[], reasoning='test')}

	mock_llm = MagicMock()
	mock_llm.with_structured_output.return_value.invoke.return_value = wrapper_result

	with ExitStack() as stack:
		stack.enter_context(patch.object(agent_core, 'create_agent', return_value=MagicMock(invoke=MagicMock(return_value=agent_result))))
		stack.enter_context(patch.object(agent_tools, 'get', return_value=[]))
		stack.enter_context(patch.object(prompt, 'prompt', return_value=[]))
		_, usage, _, wrapper_used = agent._Agent__generate_response(mock_llm, session)

	assert wrapper_used is True
	assert usage.input_tokens == 30
	assert usage.output_tokens == 13
	assert usage.total_tokens == 43

# Direct path returns only base tokens without wrapper: Success
def test_generate_response_no_wrapper_base_tokens_only(session):
	base_msg = MagicMock()
	base_msg.type = 'ai'
	base_msg.usage_metadata = {'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15}

	parsed = AgentResponse(define=[], undefine=[], reasoning='test')
	agent_result = {'messages': [base_msg], 'structured_response': parsed}

	mock_llm = MagicMock()

	with ExitStack() as stack:
		stack.enter_context(patch.object(agent_core, 'create_agent', return_value=MagicMock(invoke=MagicMock(return_value=agent_result))))
		stack.enter_context(patch.object(agent_tools, 'get', return_value=[]))
		stack.enter_context(patch.object(prompt, 'prompt', return_value=[]))
		_, usage, _, wrapper_used = agent._Agent__generate_response(mock_llm, session)

	assert wrapper_used is False
	assert usage.input_tokens == 10
	assert usage.output_tokens == 5
	assert usage.total_tokens == 15
