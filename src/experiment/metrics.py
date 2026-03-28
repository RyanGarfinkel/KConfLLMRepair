from singleton_decorator import singleton
from src.config import settings
import json

@singleton
class SessionMetrics:

	def load(self, path: str) -> dict:
		with open(path) as f:
			data = json.load(f)

		summary = data['summary']
		return {
			'status': summary['status'],
			'attempts': summary['attempts'],
			'edit_distance': summary['edit_distance'],
			'constraints': data['constraints'],
			'llm_token_usage': data['llm_token_usage'],
			'embedding_token_usage': data['embedding_token_usage'],
		}

@singleton
class ExperimentMetrics:

	def __init__(self):
		self.__completed: list[tuple[int, dict]] = []

	def record(self, i: int, data: dict, duration: float):

		data = {**data, 'duration': duration}
		self.__completed.append((i, data))

		entries = [d for _, d in self.__completed]
		n = len(entries)
		sorted_entries = sorted(self.__completed, key=lambda t: t[0])
		successes = [d for d in entries if d['status'] in ['success', 'success-maintenance']]
		total_attempts = sum(d['attempts'] for d in entries)

		with open(f'{settings.runtime.OUTPUT_DIR}/results.json', 'w') as f:
			json.dump({
				'summary': {
					'n': n,
					'successes': len([d for d in entries if d['status'] == 'success']),
					'maintenance': len([d for d in entries if d['status'] == 'success-maintenance']),
					'failures': len([d for d in entries if d['status'] == 'max-attempts-reached']),
					'initial_input_worked': len([d for d in entries if d['attempts'] == 0 and d['status'] == 'success']),
					'avg_attempts': sum(d['attempts'] for d in entries) / n,
					'avg_duration': sum(d['duration'] for d in entries) / n,
					'avg_success_edit_distance': sum(d['edit_distance'] for d in successes) / len(successes) if successes else -1,
					'avg_success_constraints': sum(d['constraints']['total'] for d in successes) / len(successes) if successes else -1,
				},
				'llm_token_usage': {
					'model': settings.agent.MODEL,
					'input_tokens': sum(d['llm_token_usage']['input_tokens'] for d in entries),
					'output_tokens': sum(d['llm_token_usage']['output_tokens'] for d in entries),
					'total_tokens': sum(d['llm_token_usage']['total_tokens'] for d in entries),
				},
				'embedding_token_usage': {
					'model': settings.agent.EMBEDDING_MODEL if settings.runtime.USE_RAG else None,
					'build_log_tokens': sum(d['embedding_token_usage']['build_log_tokens'] for d in entries),
					'boot_log_tokens': sum(d['embedding_token_usage']['boot_log_tokens'] for d in entries),
					'total_tokens': sum(d['embedding_token_usage']['total_tokens'] for d in entries),
				},
				'time': {
					'avg_duration': sum(d['duration'] for d in entries) / n,
					'avg_duration_per_attempt': sum(d['duration'] for d in entries) / total_attempts if total_attempts > 0 else -1,
				},
				'samples': [
					{
						'sample': idx + 1,
						'status': d['status'],
						'attempts': d['attempts'],
						'duration': d['duration'],
						'edit_distance': d['edit_distance'],
						'constraints': d['constraints'],
						'llm_token_usage': d['llm_token_usage'],
						'embedding_token_usage': d['embedding_token_usage'],
					} for idx, d in sorted_entries
				]
			}, f, indent=4)

session_metrics = SessionMetrics()
experiment_metrics = ExperimentMetrics()
