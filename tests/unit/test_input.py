from src.cli.repair import get_input
import click
import pytest
import os

# Patch Input: Success
def test_patch_input(tmp_config, tmp_patch, tmp_path):
	modified = f'{tmp_path}/modified.config'
	open(modified, 'w').close()

	inp = get_input(original=tmp_config, modified=modified, patch=tmp_patch)

	assert inp.original_config == os.path.abspath(tmp_config)
	assert inp.modified_config == os.path.abspath(modified)
	assert inp.patch == os.path.abspath(tmp_patch)

# Config Input: Success
def test_config_input(tmp_config, tmp_path):
	output = f'{tmp_path}/out'
	os.makedirs(output)

	inp = get_input(config=tmp_config, output=output)

	assert inp.original_config == os.path.abspath(tmp_config)
	assert inp.modified_config is None
	assert inp.patch is None
	assert output in inp.output

# No Input: Failure
def test_no_input():
	with pytest.raises(click.UsageError):
		get_input()

# Patch Required Fields: Failure
def test_patch_required_fields(tmp_config, tmp_patch):
	with pytest.raises(click.UsageError):
		get_input(modified=tmp_config, patch=tmp_patch)

	with pytest.raises(click.UsageError):
		get_input(original=tmp_config, patch=tmp_patch)

	with pytest.raises(click.UsageError):
		get_input(original=tmp_config, modified=str(tmp_patch))

# Config Required Fields: Failure
def test_config_required_fields():
	with pytest.raises(click.UsageError):
		get_input(output='out')

# Output: Default & Custom
def test_output(tmp_config, tmp_path):
	inp = get_input(config=tmp_config)
	assert inp.output == f'{tmp_path}/agent-repair'

	out = f'{tmp_path}/custom'
	os.makedirs(out)
	inp = get_input(config=tmp_config, output=out)
	assert inp.output == f'{out}/agent-repair'
