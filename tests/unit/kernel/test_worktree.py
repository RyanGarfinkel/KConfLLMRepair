from unittest.mock import patch, MagicMock, PropertyMock
from src.kernel.worktree import worktree
from src.config import KernelSettings
import sys

worktree_module = sys.modules['src.kernel.worktree']

# Create worktree: Success
def test_create_returns_path(tmp_path):
	commit = 'abc1234567890'
	expected = str(tmp_path / f'{commit[:10]}_0')
	
	with patch.object(worktree, 'main_repo'), \
		 patch.object(worktree_module, 'Repo') as mock_repo_cls, \
		 patch.object(KernelSettings, 'WORKTREE_DIR', new_callable=PropertyMock, return_value=str(tmp_path)):
		mock_repo_cls.return_value = MagicMock()
		result = worktree.create(commit)

	assert result == expected

# Create worktree with path collision: Success
def test_create_increments_path_on_collision(tmp_path):
	commit = 'abc1234567890'
	(tmp_path / f'{commit[:10]}_0').mkdir()
	expected = str(tmp_path / f'{commit[:10]}_1')

	with patch.object(worktree, 'main_repo'), \
		 patch.object(worktree_module, 'Repo') as mock_repo_cls, \
		 patch.object(KernelSettings, 'WORKTREE_DIR', new_callable=PropertyMock, return_value=str(tmp_path)):
		mock_repo_cls.return_value = MagicMock()
		result = worktree.create(commit)

	assert result == expected

# Cleanup existing worktree: Success
def test_cleanup_existing(tmp_path):
	path = str(tmp_path / 'worktree')
	tmp_path.joinpath('worktree').mkdir()

	with patch.object(worktree, 'main_repo') as mock_repo:
		result = worktree.cleanup(path)

	assert result is True
	mock_repo.git.worktree.assert_called_once_with('remove', '-f', path)

# Cleanup missing path: Success
def test_cleanup_missing_path(tmp_path):
	path = str(tmp_path / 'nonexistent')
	result = worktree.cleanup(path)
	assert result is True

# Cleanup skips kernel src directory: Success
def test_cleanup_skips_kernel_src(tmp_path):
	path = str(tmp_path)

	with patch.object(worktree, 'main_repo') as mock_repo, \
		 patch.object(worktree_module, 'settings') as mock_settings:
		mock_settings.kernel.KERNEL_SRC = path
		result = worktree.cleanup(path)

	assert result is True
	mock_repo.git.worktree.assert_not_called()

# Cleanup git fails, shutil succeeds: Success
def test_cleanup_git_fails_manual_succeeds(tmp_path):
	path = str(tmp_path / 'worktree')
	tmp_path.joinpath('worktree').mkdir()

	with patch.object(worktree, 'main_repo') as mock_repo, \
		 patch.object(worktree_module, 'shutil') as mock_shutil, \
		 patch.object(worktree_module, 'settings') as mock_settings:
		mock_settings.kernel.KERNEL_SRC = '/different/path'
		mock_repo.git.worktree.side_effect = Exception('git error')
		result = worktree.cleanup(path)

	assert result is True
	mock_shutil.rmtree.assert_called_once_with(path)

# Cleanup git and shutil both fail: Failure
def test_cleanup_both_methods_fail(tmp_path):
	path = str(tmp_path / 'worktree')
	tmp_path.joinpath('worktree').mkdir()

	with patch.object(worktree, 'main_repo') as mock_repo, \
		 patch.object(worktree_module, 'shutil') as mock_shutil, \
		 patch.object(worktree_module, 'settings') as mock_settings:
		mock_settings.kernel.KERNEL_SRC = '/different/path'
		mock_repo.git.worktree.side_effect = Exception('git error')
		mock_shutil.rmtree.side_effect = Exception('rmtree error')
		result = worktree.cleanup(path)

	assert result is False
