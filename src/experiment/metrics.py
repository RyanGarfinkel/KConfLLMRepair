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
			'path': path,
			'status': summary['status'],
			'attempts': summary['attempts'],
			'edit_distance': summary['edit_distance'],
			'llm_time': summary['total_llm_time'],
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
				'success_rate': {
					'5': len([d for d in entries if d['status'] == 'success' and d['attempts'] <= 5]) / n,
					'10': len([d for d in entries if d['status'] == 'success' and d['attempts'] <= 10]) / n,
					'15': len([d for d in entries if d['status'] == 'success' and d['attempts'] <= 15]) / n,
					'20': len([d for d in entries if d['status'] == 'success' and d['attempts'] <= 20]) / n,
				},
				'llm_token_usage': {
					'model': settings.agent.MODEL,
					'total': {
						'input_tokens': sum(d['llm_token_usage']['input_tokens'] for d in entries),
						'output_tokens': sum(d['llm_token_usage']['output_tokens'] for d in entries),
						'total_tokens': sum(d['llm_token_usage']['total_tokens'] for d in entries),
					},
					'avg_per_repair': {
						'input_tokens': sum(d['llm_token_usage']['input_tokens'] for d in entries) / n,
						'output_tokens': sum(d['llm_token_usage']['output_tokens'] for d in entries) / n,
						'total_tokens': sum(d['llm_token_usage']['total_tokens'] for d in entries) / n,
					},
					'avg_per_attempt': {
						'input_tokens': sum(d['llm_token_usage']['input_tokens'] for d in entries) / total_attempts if total_attempts > 0 else -1,
						'output_tokens': sum(d['llm_token_usage']['output_tokens'] for d in entries) / total_attempts if total_attempts > 0 else -1,
						'total_tokens': sum(d['llm_token_usage']['total_tokens'] for d in entries) / total_attempts if total_attempts > 0 else -1,
					}
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
						'path': d['path'],
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
