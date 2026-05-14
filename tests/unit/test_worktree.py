from unittest.mock import patch, MagicMock
from src.kernel.worktree import worktree

# Create worktree: Success
def test_create_returns_path(tmp_path):
	commit = 'abc1234567890'
	expected = str(tmp_path / f'{commit[:10]}_0')
	with patch.object(worktree, 'main_repo') as mock_repo, \
		 patch('src.kernel.worktree.Repo') as mock_repo_cls, \
		 patch('src.kernel.worktree.settings.kernel.WORKTREE_DIR', str(tmp_path)):
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
