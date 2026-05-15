from src.cli.repair import get_input
from src.models.input import Input
import pytest
import click
import os

# Patch Input: Success
def test_patch_input(tmp_config, tmp_patch, tmp_path):
	modified = f'{tmp_path}/modified.config'
	open(modified, 'w').close()

	inp = get_input(original=tmp_config, modified=modified, patch=tmp_patch)

	assert inp.original_config == os.path.abspath(tmp_config)
	assert inp.modified_config == os.path.abspath(modified)
	assert inp.patch == os.path.abspath(tmp_patch)

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

# Define field from constraints file: Success
def test_define_from_constraints(tmp_path):
	config = tmp_path / 'test.config'
	config.touch()
	constraints = tmp_path / 'constraints.txt'
	constraints.write_text('CONFIG_NET\n!CONFIG_UNUSED\nCONFIG_SMP\n')
	inp = Input(original_config=str(config), hard_constraints=str(constraints))
	assert 'CONFIG_NET' in inp.define
	assert 'CONFIG_SMP' in inp.define
	assert 'CONFIG_UNUSED' not in inp.define

# Undefine field from constraints file: Success
def test_undefine_from_constraints(tmp_path):
	config = tmp_path / 'test.config'
	config.touch()
	constraints = tmp_path / 'constraints.txt'
	constraints.write_text('CONFIG_NET\n!CONFIG_UNUSED\n!CONFIG_OLD\n')
	inp = Input(original_config=str(config), hard_constraints=str(constraints))
	assert 'CONFIG_UNUSED' in inp.undefine
	assert 'CONFIG_OLD' in inp.undefine
	assert 'CONFIG_NET' not in inp.undefine

# Define empty when no constraints file: Success
def test_define_empty_without_constraints(tmp_path):
	config = tmp_path / 'test.config'
	config.touch()
	inp = Input(original_config=str(config))
	assert inp.define == set()
	assert inp.undefine == set()
