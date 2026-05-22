from unittest.mock import patch, MagicMock
from src.experiment.metrics import session_metrics, experiment_metrics
import sys
import json
import pytest

metrics_module = sys.modules['src.experiment.metrics']


def _sample_data(status='success', attempts=3, edit_distance=5, constraints_total=2,
	input_tokens=100, output_tokens=50, total_tokens=150):
	return {
		'path': '/fake/path/summary.json',
		'status': status,
		'attempts': attempts,
		'edit_distance': edit_distance,
		'constraints': {'defines': 1, 'undefines': 1, 'total': constraints_total},
		'llm_token_usage': {'input_tokens': input_tokens, 'output_tokens': output_tokens, 'total_tokens': total_tokens},
		'embedding_token_usage': {'build_log_tokens': 10, 'boot_log_tokens': 5, 'total_tokens': 15},
	}


@pytest.fixture(autouse=True)
def reset_experiment_metrics():
	experiment_metrics._ExperimentMetrics__completed = []
	yield
	experiment_metrics._ExperimentMetrics__completed = []


@pytest.fixture
def mock_settings(tmp_path):
	mock = MagicMock()
	mock.runtime.OUTPUT_DIR = str(tmp_path)
	mock.agent.MODEL = 'test-model'
	mock.runtime.USE_RAG = False
	mock.agent.EMBEDDING_MODEL = 'test-embed'
	return mock


def _load_results(tmp_path):
	with open(tmp_path / 'results.json', encoding='utf-8') as f:
		return json.load(f)


# Load extracts correct fields: Success
def test_load_extracts_correct_fields(tmp_path):
	summary_path = f'{tmp_path}/summary.json'
	data = {
		'summary': {
			'status': 'success',
			'attempts': 4,
			'edit_distance': 7,
			'total_llm_time': 12.5,
		},
		'constraints': {'defines': 2, 'undefines': 1, 'total': 3},
		'llm_token_usage': {'input_tokens': 200, 'output_tokens': 80, 'total_tokens': 280},
		'embedding_token_usage': {'build_log_tokens': 20, 'boot_log_tokens': 10, 'total_tokens': 30},
	}
	with open(summary_path, 'w', encoding='utf-8') as f:
		json.dump(data, f)

	result = session_metrics.load(summary_path)

	assert result['path'] == summary_path
	assert result['status'] == 'success'
	assert result['attempts'] == 4
	assert result['edit_distance'] == 7
	assert result['llm_time'] == 12.5
	assert result['constraints'] == {'defines': 2, 'undefines': 1, 'total': 3}
	assert result['llm_token_usage'] == {'input_tokens': 200, 'output_tokens': 80, 'total_tokens': 280}
	assert result['embedding_token_usage'] == {'build_log_tokens': 20, 'boot_log_tokens': 10, 'total_tokens': 30}

# Single success record writes correct summary: Success
def test_single_success_record(tmp_path, mock_settings):
	with patch.object(metrics_module, 'settings', mock_settings):
		experiment_metrics.record(0, _sample_data(status='success', attempts=3), duration=10.0)

	result = _load_results(tmp_path)

	assert result['summary']['n'] == 1
	assert result['summary']['successes'] == 1
	assert result['summary']['failures'] == 0
	assert result['summary']['avg_attempts'] == 3
	assert len(result['samples']) == 1

# Multiple records aggregate status counts: Success
def test_multiple_records_aggregate_status_counts(tmp_path, mock_settings):
	with patch.object(metrics_module, 'settings', mock_settings):
		experiment_metrics.record(0, _sample_data(status='success'), duration=10.0)
		experiment_metrics.record(1, _sample_data(status='success-maintenance'), duration=10.0)
		experiment_metrics.record(2, _sample_data(status='max-attempts-reached'), duration=10.0)

	result = _load_results(tmp_path)

	assert result['summary']['successes'] == 1
	assert result['summary']['maintenance'] == 1
	assert result['summary']['failures'] == 1

# Success rate buckets computed correctly: Success
def test_success_rate_buckets(tmp_path, mock_settings):
	with patch.object(metrics_module, 'settings', mock_settings):
		experiment_metrics.record(0, _sample_data(status='success', attempts=2), duration=5.0)
		experiment_metrics.record(1, _sample_data(status='success', attempts=8), duration=5.0)
		experiment_metrics.record(2, _sample_data(status='success', attempts=12), duration=5.0)
		experiment_metrics.record(3, _sample_data(status='success', attempts=18), duration=5.0)

	result = _load_results(tmp_path)
	rates = result['success_rate']

	assert rates['5'] == 1 / 4
	assert rates['10'] == 2 / 4
	assert rates['15'] == 3 / 4
	assert rates['20'] == 4 / 4

# initial_input_worked counts zero-attempt successes: Success
def test_initial_input_worked(tmp_path, mock_settings):
	with patch.object(metrics_module, 'settings', mock_settings):
		experiment_metrics.record(0, _sample_data(status='success', attempts=0), duration=5.0)

	result = _load_results(tmp_path)

	assert result['summary']['initial_input_worked'] == 1

# No successes gives -1 for avg_success_edit_distance: Success
def test_no_successes_gives_negative_one(tmp_path, mock_settings):
	with patch.object(metrics_module, 'settings', mock_settings):
		experiment_metrics.record(0, _sample_data(status='max-attempts-reached', attempts=5), duration=10.0)

	result = _load_results(tmp_path)

	assert result['summary']['avg_success_edit_distance'] == -1
	assert result['summary']['avg_success_constraints'] == -1

# total_attempts=0 gives -1 for avg_per_attempt: Success
def test_zero_total_attempts_gives_negative_one(tmp_path, mock_settings):
	with patch.object(metrics_module, 'settings', mock_settings):
		experiment_metrics.record(0, _sample_data(status='success', attempts=0), duration=5.0)

	result = _load_results(tmp_path)
	avg = result['llm_token_usage']['avg_per_attempt']

	assert avg['input_tokens'] == -1
	assert avg['output_tokens'] == -1
	assert avg['total_tokens'] == -1

# Token usage sums correctly across records: Success
def test_token_usage_sums(tmp_path, mock_settings):
	with patch.object(metrics_module, 'settings', mock_settings):
		experiment_metrics.record(0, _sample_data(input_tokens=100, output_tokens=50, total_tokens=150), duration=5.0)
		experiment_metrics.record(1, _sample_data(input_tokens=200, output_tokens=80, total_tokens=280), duration=5.0)

	result = _load_results(tmp_path)
	totals = result['llm_token_usage']['total']

	assert totals['input_tokens'] == 300
	assert totals['output_tokens'] == 130
	assert totals['total_tokens'] == 430

# samples list is sorted by index: Success
def test_samples_sorted_by_index(tmp_path, mock_settings):
	data_a = _sample_data(status='success', attempts=1)
	data_a['path'] = '/path/a'
	data_b = _sample_data(status='max-attempts-reached', attempts=5)
	data_b['path'] = '/path/b'

	with patch.object(metrics_module, 'settings', mock_settings):
		experiment_metrics.record(2, data_b, duration=5.0)
		experiment_metrics.record(0, data_a, duration=5.0)

	result = _load_results(tmp_path)
	samples = result['samples']

	assert samples[0]['path'] == '/path/a'
	assert samples[1]['path'] == '/path/b'

# Duration averages correctly: Success
def test_duration_averages(tmp_path, mock_settings):
	with patch.object(metrics_module, 'settings', mock_settings):
		experiment_metrics.record(0, _sample_data(attempts=3), duration=20.0)
		experiment_metrics.record(1, _sample_data(attempts=3), duration=40.0)

	result = _load_results(tmp_path)

	assert result['time']['avg_duration'] == 30.0
