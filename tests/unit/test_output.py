from unittest.mock import patch, MagicMock
from src.models import Attempt, Input
from contextlib import ExitStack
from src.core.agent import agent
from src.config import settings
from src.agent import Session
import pytest

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

def _attempt(id, dir, config=None, boot='no'):
	return Attempt(id=id, dir=str(dir), config=config, boot_succeeded=boot)

def _run_repair(repair_input, initial, side_effect):
	with ExitStack() as stack:
		stack.enter_context(patch.object(agent, '_Agent__make_dir'))
		stack.enter_context(patch.object(agent, '_Agent__inital_attempt', return_value=initial))
		stack.enter_context(patch.object(agent, '_Agent__attempt', side_effect=side_effect))
		stack.enter_context(patch('src.core.agent.model.get_llm', return_value=MagicMock()))
		stack.enter_context(patch.object(Session, 'save'))
		mock_copy = stack.enter_context(patch('src.core.agent.shutil.copyfile'))
		agent.repair(repair_input, MagicMock())
	return mock_copy

# Repair output: Success
def test_success(repair_input, tmp_path):
	settings.agent.MAX_ITERATIONS = 2
	output_dir = str(tmp_path / 'out')
	settings.runtime.OUTPUT_DIR = output_dir

	repaired_config = str(tmp_path / 'repaired.config')
	initial = _attempt(0, tmp_path)

	def append_success(llm, kernel, session):
		session.attempts.append(_attempt(1, tmp_path, config=repaired_config, boot='yes'))

	mock_copy = _run_repair(repair_input, initial, append_success)
	mock_copy.assert_called_once_with(repaired_config, f'{output_dir}/repaired.config')

# Repair output: Success (maintenance)
def test_success_maintenance(repair_input, tmp_path):
	settings.agent.MAX_ITERATIONS = 2
	output_dir = str(tmp_path / 'out')
	settings.runtime.OUTPUT_DIR = output_dir

	maintenance_config = str(tmp_path / 'maintenance.config')
	initial = _attempt(0, tmp_path)
	call_count = {'n': 0}

	def append_attempts(llm, kernel, session):
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
	output_dir = str(tmp_path / 'out')
	settings.runtime.OUTPUT_DIR = output_dir

	initial = _attempt(0, tmp_path)
	call_count = {'n': 0}

	def append_failed(llm, kernel, session):
		call_count['n'] += 1
		session.attempts.append(_attempt(call_count['n'], tmp_path))

	mock_copy = _run_repair(repair_input, initial, append_failed)
	mock_copy.assert_not_called()
