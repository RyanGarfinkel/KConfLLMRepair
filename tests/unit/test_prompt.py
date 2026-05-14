from src.agent.prompt import prompt
from src.models import Attempt
from src.agent import Session

def _session(hard_define=set(), hard_undefine=set()):
	return Session(config='/fake/config', output='/fake/output', hard_define=hard_define, hard_undefine=hard_undefine)

def _attempt(id, boot='no', build_summary=None, boot_summary=None):
	return Attempt(id=id, dir='/fake/dir', boot_succeeded=boot, build_summary=build_summary, boot_summary=boot_summary)

# Hard constraints in system prompt: Success
def test_hard_constraints_in_system():
	session = _session(hard_define={'CONFIG_NET'}, hard_undefine={'CONFIG_UNUSED'})
	content = prompt.system(session).content
	assert 'CONFIG_NET' in content
	assert 'CONFIG_UNUSED' in content

# History in user prompt: Success
def test_history_in_user():
	session = _session()
	session.attempts = [
		_attempt(0),
		_attempt(1),
		_attempt(2),
	]
	content = prompt.user(session).content
	assert 'Initial config test' in content
	assert 'Attempt 1' in content

# Current build failure in user prompt: Success
def test_current_build_failure_in_user():
	session = _session()
	session.attempts = [
		_attempt(0),
		_attempt(1, build_summary='42: error: undeclared CONFIG_FOO'),
		_attempt(2),
	]
	content = prompt.user(session).content
	assert 'CURRENT BUILD ERRORS' in content
	assert 'CONFIG_FOO' in content

# Current boot failure in user prompt: Success
def test_current_boot_failure_in_user():
	session = _session()
	session.attempts = [
		_attempt(0),
		_attempt(1, boot='panic', boot_summary='100: Kernel panic - not syncing: VFS'),
		_attempt(2),
	]
	content = prompt.user(session).content
	assert 'CURRENT BOOT FAILURE' in content
	assert 'Kernel panic' in content
