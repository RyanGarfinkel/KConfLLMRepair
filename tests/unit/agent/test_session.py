from src.models import Attempt, LLMUsage, EmbeddingUsage
from src.models.response import AgentResponse
from src.agent.session import Session
from unittest.mock import patch, MagicMock
from src.config import settings
import json
import sys
import pytest

session_module = sys.modules['src.agent.session']

@pytest.fixture(autouse=True)
def restore_max_iterations():
	original = settings.agent.MAX_ITERATIONS
	yield
	settings.agent.MAX_ITERATIONS = original

def _attempt(id, boot='no', config=None, build_time=0.0, boot_time=0.0, llm_time=0.0):
	return Attempt(id=id, dir='/fake', boot_succeeded=boot, config=config,
	               build_time=build_time, boot_time=boot_time, llm_time=llm_time)

def _session():
	return Session(config='/fake/base.config', output='/fake/output')

# latest with no attempts: Success
def test_latest_no_attempts():
	session = _session()
	assert session.latest == '/fake/base.config'

# latest with attempts: Success
def test_latest_with_attempts():
	session = _session()
	session.attempts = [_attempt(0, config='/fake/a.config'), _attempt(1, config='/fake/b.config')]
	assert session.latest == '/fake/b.config'

# status initialized: Success
def test_status_initialized():
	session = _session()
	assert session.status == 'initialized'

# status success: Success
def test_status_success():
	session = _session()
	session.attempts = [_attempt(0), _attempt(1, boot='yes')]
	assert session.status == 'success'

# status success-maintenance: Success
def test_status_success_maintenance():
	settings.agent.MAX_ITERATIONS = 1
	session = _session()
	session.attempts = [_attempt(0), _attempt(1, boot='maintenance')]
	assert session.status == 'success-maintenance'

# status max-attempts-reached: Success
def test_status_max_attempts_reached():
	settings.agent.MAX_ITERATIONS = 1
	session = _session()
	session.attempts = [_attempt(0), _attempt(1, boot='no')]
	assert session.status == 'max-attempts-reached'

# status in-progress: Success
def test_status_in_progress():
	settings.agent.MAX_ITERATIONS = 5
	session = _session()
	session.attempts = [_attempt(0), _attempt(1, boot='no')]
	assert session.status == 'in-progress'

# token_usage sums across attempts: Success
def test_token_usage_sum():
	session = _session()
	session.attempts = [
		_attempt(0),
		_attempt(1),
	]
	session.attempts[0].token_usage = LLMUsage(input_tokens=10, output_tokens=5, total_tokens=15)
	session.attempts[1].token_usage = LLMUsage(input_tokens=20, output_tokens=10, total_tokens=30)
	usage = session.token_usage
	assert usage.input_tokens == 30
	assert usage.output_tokens == 15
	assert usage.total_tokens == 45

# total_llm_time sums across attempts: Success
def test_total_llm_time():
	session = _session()
	session.attempts = [_attempt(0, llm_time=1.5), _attempt(1, llm_time=2.5)]
	assert session.total_llm_time == 4.0

# total_build_time sums across attempts: Success
def test_total_build_time():
	session = _session()
	session.attempts = [_attempt(0, build_time=3.0), _attempt(1, build_time=7.0)]
	assert session.total_build_time == 10.0

# total_boot_time sums across attempts: Success
def test_total_boot_time():
	session = _session()
	session.attempts = [_attempt(0, boot_time=2.0), _attempt(1, boot_time=4.0)]
	assert session.total_boot_time == 6.0

# embedding_usage sums across attempts: Success
def test_embedding_usage_sum():
	session = _session()
	a0 = _attempt(0)
	a1 = _attempt(1)
	object.__setattr__(a0, 'embedding_usage', EmbeddingUsage(build_log_tokens=100, boot_log_tokens=50))
	object.__setattr__(a1, 'embedding_usage', EmbeddingUsage(build_log_tokens=200, boot_log_tokens=100))
	session.attempts = [a0, a1]
	usage = session.embedding_usage
	assert usage.build_log_tokens == 300
	assert usage.boot_log_tokens == 150

# constraints when not success or maintenance: Success
def test_constraints_not_success():
	session = _session()
	session.attempts = [_attempt(0), _attempt(1, boot='no')]
	result = session.constraints
	assert result == {'defines': 0, 'undefines': 0, 'total': 0}

# constraints when success with response: Success
def test_constraints_success_with_response():
	session = _session()
	response = AgentResponse(define=['CONFIG_X', 'CONFIG_Y'], undefine=['CONFIG_Z'], reasoning='test')
	attempt = Attempt(id=1, dir='/fake', boot_succeeded='yes', response=response)
	session.attempts = [_attempt(0), attempt]
	result = session.constraints
	assert result == {'defines': 2, 'undefines': 1, 'total': 3}

# constraints when success but no response: Success
def test_constraints_success_no_response():
	session = _session()
	attempt = Attempt(id=1, dir='/fake', boot_succeeded='yes', response=None)
	session.attempts = [_attempt(0), attempt]
	result = session.constraints
	assert result == {'defines': 0, 'undefines': 0, 'total': 0}

# edits when not success: Success
def test_edits_not_success():
	session = _session()
	session.attempts = [_attempt(0), _attempt(1, boot='no')]
	edits, distance = session.edits
	assert edits == []
	assert distance == -1

# edits when success calls diffconfig.compare: Success
def test_edits_success():
	session = _session()
	session.attempts = [_attempt(0), _attempt(1, boot='yes', config='/fake/repaired.config')]
	with patch.object(session_module.diffconfig, 'compare', return_value=(['line1', 'line2'], 2)) as mock_compare:
		edits, distance = session.edits
	mock_compare.assert_called_once_with('/fake/base.config', '/fake/repaired.config')
	assert edits == ['line1', 'line2']
	assert distance == 2

# save writes valid JSON to file: Success
def test_save(tmp_path):
	session = _session()
	with patch.object(session_module.diffconfig, 'compare', return_value=([], 0)):
		with patch.object(session_module.settings.kernel, 'ARCH', 'x86_64'):
			out_path = f'{tmp_path}/summary.json'
			session.save(out_path)
	with open(out_path, 'r') as f:
		data = json.load(f)
	assert 'summary' in data
	assert data['summary']['status'] == 'initialized'
