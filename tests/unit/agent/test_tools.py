from unittest.mock import patch
from src.agent.tools import agent_tools
from src.agent.session import Session
from src.models import Attempt
import sys

tools_module = sys.modules['src.agent.tools']

def _session(tmp_path, build_log=None, boot_log=None, patch_path=None, config=None):
	base = config or f'{tmp_path}/base.config'
	open(base, 'w').close()
	session = Session(config=base, output=str(tmp_path), patch=patch_path)
	prev = Attempt(id=0, dir=str(tmp_path), build_log=build_log, boot_log=boot_log)
	current = Attempt(id=1, dir=str(tmp_path))
	session.attempts = [prev, current]
	return session

# grep finds matching lines: Success
def test_grep_finds_matching_lines(tmp_path):
	f = tmp_path / 'log.txt'
	f.write_text('line one\nline two\nerror: something broke\nline four\nline five\n')
	result = agent_tools._AgentTools__grep(str(f), 'error')
	assert len(result) == 1
	assert result[0].startswith('3: ')
	assert 'error: something broke' in result[0]

# grep is case-insensitive: Success
def test_grep_case_insensitive(tmp_path):
	f = tmp_path / 'log.txt'
	f.write_text('ERROR: something\n')
	result = agent_tools._AgentTools__grep(str(f), 'error')
	assert len(result) == 1
	assert 'ERROR: something' in result[0]

# grep returns no-match message when nothing found: Success
def test_grep_no_match(tmp_path):
	f = tmp_path / 'log.txt'
	f.write_text('nothing relevant here\n')
	result = agent_tools._AgentTools__grep(str(f), 'zzznotfound')
	assert len(result) == 1
	assert 'No matches found' in result[0]

# grep returns not-exist message for missing file: Failure
def test_grep_missing_file(tmp_path):
	missing = f'{tmp_path}/nonexistent.txt'
	result = agent_tools._AgentTools__grep(missing, 'error')
	assert len(result) == 1
	assert missing in result[0]

# grep falls back to literal on invalid regex: Success
def test_grep_invalid_regex_fallback(tmp_path):
	f = tmp_path / 'log.txt'
	f.write_text('[unclosed bracket here\n')
	result = agent_tools._AgentTools__grep(str(f), '[unclosed')
	assert len(result) == 1
	assert '[unclosed bracket here' in result[0]

# grep truncates at 50 matches: Success
def test_grep_truncates_at_50(tmp_path):
	f = tmp_path / 'log.txt'
	f.write_text('\n'.join([f'error: line {i}' for i in range(60)]) + '\n')
	result = agent_tools._AgentTools__grep(str(f), 'error')
	assert len(result) == 51
	assert 'more matches not shown' in result[-1]

# chunk returns lines centered on target: Success
def test_chunk_centered(tmp_path):
	f = tmp_path / 'log.txt'
	f.write_text('\n'.join([f'line {i}' for i in range(1, 101)]) + '\n')
	result = agent_tools._AgentTools__chunk(str(f), 50)
	line_numbers = [int(entry.split(':')[0]) for entry in result]
	assert min(line_numbers) <= 26
	assert max(line_numbers) >= 74

# chunk clamps at file start: Success
def test_chunk_clamps_at_start(tmp_path):
	f = tmp_path / 'log.txt'
	f.write_text('\n'.join([f'line {i}' for i in range(1, 101)]) + '\n')
	result = agent_tools._AgentTools__chunk(str(f), 5)
	first_line_number = int(result[0].split(':')[0])
	assert first_line_number == 1

# chunk clamps at file end: Success
def test_chunk_clamps_at_end(tmp_path):
	f = tmp_path / 'log.txt'
	f.write_text('\n'.join([f'line {i}' for i in range(1, 101)]) + '\n')
	result = agent_tools._AgentTools__chunk(str(f), 98)
	last_line_number = int(result[-1].split(':')[0])
	assert last_line_number == 100

# chunk returns not-exist message for missing file: Failure
def test_chunk_missing_file(tmp_path):
	missing = f'{tmp_path}/nonexistent.txt'
	result = agent_tools._AgentTools__chunk(missing, 10)
	assert len(result) == 1
	assert missing in result[0]

# search_config finds assigned option: Success
def test_search_config_assigned(tmp_path):
	f = tmp_path / '.config'
	f.write_text('CONFIG_NET=y\nCONFIG_UNUSED=m\n')
	result = agent_tools._AgentTools__search_config(str(f), ['CONFIG_NET'])
	assert result == ['CONFIG_NET=y']

# search_config finds disabled option: Success
def test_search_config_disabled(tmp_path):
	f = tmp_path / '.config'
	f.write_text('# CONFIG_OLD is not set\n')
	result = agent_tools._AgentTools__search_config(str(f), ['CONFIG_OLD'])
	assert result == ['# CONFIG_OLD is not set']

# search_config reports missing option: Success
def test_search_config_missing_option(tmp_path):
	f = tmp_path / '.config'
	f.write_text('CONFIG_NET=y\n')
	result = agent_tools._AgentTools__search_config(str(f), ['CONFIG_MISSING'])
	assert len(result) == 1
	assert 'not found' in result[0]

# search_config returns not-exist message for missing file: Failure
def test_search_config_missing_file(tmp_path):
	missing = f'{tmp_path}/nonexistent.config'
	result = agent_tools._AgentTools__search_config(missing, ['CONFIG_NET'])
	assert len(result) == 1
	assert missing in result[0]

# get always includes search_original_config: Success
def test_get_always_includes_search_original_config(tmp_path):
	session = _session(tmp_path)
	with patch.object(tools_module, 'settings') as mock_settings:
		mock_settings.runtime.USE_RAG = False
		tools = agent_tools.get(session)
	names = [t.name for t in tools]
	assert 'search_original_config' in names

# get includes search_latest_config when prev config differs from base: Success
def test_get_includes_search_latest_config_when_different(tmp_path):
	other_config = f'{tmp_path}/modified.config'
	open(other_config, 'w').close()
	session = _session(tmp_path)
	session.attempts[-2].config = other_config
	with patch.object(tools_module, 'settings') as mock_settings:
		mock_settings.runtime.USE_RAG = False
		tools = agent_tools.get(session)
	names = [t.name for t in tools]
	assert 'search_latest_config' in names

# grep_build_log tool logs tool call: Success
def test_grep_build_log_logs_tool_call(tmp_path):
	build_log = f'{tmp_path}/build.log'
	with open(build_log, 'w') as fh:
		fh.write('error: undefined reference to CONFIG_FOO\n')
	session = _session(tmp_path, build_log=build_log)
	with patch.object(tools_module, 'settings') as mock_settings:
		mock_settings.runtime.USE_RAG = False
		tools = agent_tools.get(session)
	tool = next(t for t in tools if t.name == 'grep_build_log')
	tool.invoke({'pattern': 'error'})
	assert len(session.attempts[-1].tool_calls) == 1
	assert session.attempts[-1].tool_calls[0].name == 'grep_build_log'

# grep_boot_log tool returns matches from boot log: Success
def test_grep_boot_log_returns_matches(tmp_path):
	boot_log = f'{tmp_path}/boot.log'
	with open(boot_log, 'w') as fh:
		fh.write('Kernel panic - not syncing: VFS\n')
	session = _session(tmp_path, boot_log=boot_log)
	with patch.object(tools_module, 'settings') as mock_settings:
		mock_settings.runtime.USE_RAG = False
		tools = agent_tools.get(session)
	tool = next(t for t in tools if t.name == 'grep_boot_log')
	result = tool.invoke({'pattern': 'panic'})
	assert 'Kernel panic' in result

# patch tools included when session has a patch: Success
def test_get_includes_patch_tools_when_patch_set(tmp_path):
	patch_file = f'{tmp_path}/changes.patch'
	open(patch_file, 'w').close()
	session = _session(tmp_path, patch_path=patch_file)
	with patch.object(tools_module, 'settings') as mock_settings:
		mock_settings.runtime.USE_RAG = False
		tools = agent_tools.get(session)
	names = [t.name for t in tools]
	assert 'grep_patch' in names
	assert 'chunk_patch' in names

# patch tools absent when session has no patch: Success
def test_get_excludes_patch_tools_when_no_patch(tmp_path):
	session = _session(tmp_path)
	with patch.object(tools_module, 'settings') as mock_settings:
		mock_settings.runtime.USE_RAG = False
		tools = agent_tools.get(session)
	names = [t.name for t in tools]
	assert 'grep_patch' not in names
	assert 'chunk_patch' not in names
