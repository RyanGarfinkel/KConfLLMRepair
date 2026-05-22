from unittest.mock import patch, MagicMock
from src.experiment.sample import sampler
from src.models import Sample
import json
import sys

sample_module = sys.modules['src.experiment.sample']

def _sample(**kwargs):
	defaults = dict(
		sample_dir='/fake/sample_0',
		kernel_src='/fake/src',
		kernel_version='6.1.0',
		end_commit='abc123',
		end_commit_date='2024-01-01T00:00:00',
	)
	return Sample(**{**defaults, **kwargs})

# Save writes sampling.json with correct structure: Success
def test_save_writes_correct_structure(tmp_path):
	samples = [_sample(sample_dir=f'/fake/sample_{i}') for i in range(2)]
	summary = {'kernel_version': '6.1.0', 'n': 2}

	with patch.object(sample_module, 'settings') as mock_settings:
		mock_settings.runtime.OUTPUT_DIR = str(tmp_path)
		sampler._Sampler__save(summary, samples)

	with open(tmp_path / 'sampling.json', 'r') as f:
		data = json.load(f)

	assert data['summary']['completed'] == 2
	assert len(data['samples']) == 2
	assert 'sample_dir' in data['samples'][0]
	assert 'end_commit' in data['samples'][0]

# Save counts build_failed correctly: Success
def test_save_counts_build_failed(tmp_path):
	samples = [_sample(built=False), _sample(built=True, boot_status='no')]
	summary = {'n': 2}

	with patch.object(sample_module, 'settings') as mock_settings:
		mock_settings.runtime.OUTPUT_DIR = str(tmp_path)
		sampler._Sampler__save(summary, samples)

	with open(tmp_path / 'sampling.json', 'r') as f:
		data = json.load(f)

	assert data['summary']['build_failed'] == 1

# Save counts boot_failed correctly: Success
def test_save_counts_boot_failed(tmp_path):
	samples = [_sample(built=True, boot_status='panic'), _sample(built=True, boot_status='yes')]
	summary = {'n': 2}

	with patch.object(sample_module, 'settings') as mock_settings:
		mock_settings.runtime.OUTPUT_DIR = str(tmp_path)
		sampler._Sampler__save(summary, samples)

	with open(tmp_path / 'sampling.json', 'r') as f:
		data = json.load(f)

	assert data['summary']['boot_failed'] == 1

# Save skips boot_failed count when built is None: Success
def test_save_boot_failed_skipped_when_built_none(tmp_path):
	samples = [_sample(built=None, boot_status='panic')]
	summary = {'n': 1}

	with patch.object(sample_module, 'settings') as mock_settings:
		mock_settings.runtime.OUTPUT_DIR = str(tmp_path)
		sampler._Sampler__save(summary, samples)

	with open(tmp_path / 'sampling.json', 'r') as f:
		data = json.load(f)

	assert data['summary']['boot_failed'] == 0

# read_samples returns correct number of samples: Success
def test_read_samples_returns_n(tmp_path):
	raw = [_sample(sample_dir=f'/fake/sample_{i}').model_dump() for i in range(5)]
	(tmp_path / 'sampling.json').write_text(json.dumps({'samples': raw}))

	with patch.object(sample_module, 'settings') as mock_settings:
		mock_settings.runtime.OUTPUT_DIR = str(tmp_path)
		result = sampler.read_samples(3)

	assert len(result) == 3

# read_samples returns Sample instances with correct fields: Success
def test_read_samples_returns_sample_objects(tmp_path):
	raw = [_sample(sample_dir='/fake/sample_0', end_commit='deadbeef').model_dump()]
	(tmp_path / 'sampling.json').write_text(json.dumps({'samples': raw}))

	with patch.object(sample_module, 'settings') as mock_settings:
		mock_settings.runtime.OUTPUT_DIR = str(tmp_path)
		result = sampler.read_samples(5)

	assert len(result) == 1
	assert isinstance(result[0], Sample)
	assert result[0].end_commit == 'deadbeef'

# read_samples handles empty samples list: Success
def test_read_samples_empty(tmp_path):
	(tmp_path / 'sampling.json').write_text(json.dumps({'samples': []}))

	with patch.object(sample_module, 'settings') as mock_settings:
		mock_settings.runtime.OUTPUT_DIR = str(tmp_path)
		result = sampler.read_samples(10)

	assert result == []

# Sample random configs returns correct summary: Success
def test_sample_random_configs_summary(tmp_path):
	mock_repo = MagicMock()
	mock_repo.head.commit.hexsha = 'abc123'
	mock_repo.head.commit.committed_datetime.isoformat.return_value = '2024-01-01T00:00:00'

	mock_kernel = MagicMock()
	mock_kernel.version = '6.1.0'

	with patch.object(sample_module, 'main_repo', mock_repo), \
	     patch.object(sample_module, 'settings') as mock_settings, \
	     patch('src.experiment.sample.Kernel', return_value=mock_kernel):
		mock_settings.kernel.KERNEL_SRC = str(tmp_path)
		mock_settings.runtime.OUTPUT_DIR = str(tmp_path)
		summary, _ = sampler._Sampler__sample_random_configs(2)

	assert summary['kernel_version'] == '6.1.0'
	assert summary['end_commit'] == 'abc123'
	assert summary['end_commit_date'] == '2024-01-01T00:00:00'
	assert summary['n'] == 2

# Sample random configs returns n samples: Success
def test_sample_random_configs_returns_n(tmp_path):
	mock_repo = MagicMock()
	mock_repo.head.commit.hexsha = 'abc123'
	mock_repo.head.commit.committed_datetime.isoformat.return_value = '2024-01-01T00:00:00'

	mock_kernel = MagicMock()
	mock_kernel.version = '6.1.0'

	with patch.object(sample_module, 'main_repo', mock_repo), \
	     patch.object(sample_module, 'settings') as mock_settings, \
	     patch('src.experiment.sample.Kernel', return_value=mock_kernel):
		mock_settings.kernel.KERNEL_SRC = str(tmp_path)
		mock_settings.runtime.OUTPUT_DIR = str(tmp_path)
		_, samples = sampler._Sampler__sample_random_configs(4)

	assert len(samples) == 4

# Sample random configs samples have unique seeds: Success
def test_sample_random_configs_unique_seeds(tmp_path):
	mock_repo = MagicMock()
	mock_repo.head.commit.hexsha = 'abc123'
	mock_repo.head.commit.committed_datetime.isoformat.return_value = '2024-01-01T00:00:00'

	mock_kernel = MagicMock()
	mock_kernel.version = '6.1.0'

	with patch.object(sample_module, 'main_repo', mock_repo), \
	     patch.object(sample_module, 'settings') as mock_settings, \
	     patch('src.experiment.sample.Kernel', return_value=mock_kernel):
		mock_settings.kernel.KERNEL_SRC = str(tmp_path)
		mock_settings.runtime.OUTPUT_DIR = str(tmp_path)
		_, samples = sampler._Sampler__sample_random_configs(10)

	seeds = [s.seed for s in samples]
	assert len(seeds) == len(set(seeds))

# Sample random configs samples have correct end_commit: Success
def test_sample_random_configs_end_commit(tmp_path):
	mock_repo = MagicMock()
	mock_repo.head.commit.hexsha = 'deadbeef'
	mock_repo.head.commit.committed_datetime.isoformat.return_value = '2024-06-01T00:00:00'

	mock_kernel = MagicMock()
	mock_kernel.version = '6.1.0'

	with patch.object(sample_module, 'main_repo', mock_repo), \
	     patch.object(sample_module, 'settings') as mock_settings, \
	     patch('src.experiment.sample.Kernel', return_value=mock_kernel):
		mock_settings.kernel.KERNEL_SRC = str(tmp_path)
		mock_settings.runtime.OUTPUT_DIR = str(tmp_path)
		_, samples = sampler._Sampler__sample_random_configs(3)

	assert all(s.end_commit == 'deadbeef' for s in samples)
