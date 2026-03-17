from singleton_decorator import singleton
from src.utils import file_lock
from src.config import settings
from src.agent import Session
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
			'duration': summary['duration'],
			'edit_distance': summary['edit_distance'],
			'constraints': data['constraints'],
			'llm_token_usage': data['llm_token_usage'],
			'embedding_token_usage': data['embedding_token_usage'],
		}

@singleton
class ExperimentMetrics:

	def __init__(self):
		self.__completed: list[tuple[int, Session]] = []

	def record(self, i: int, session: Session):

		self.__completed.append((i, session))

		sessions = [s for _, s in self.__completed]
		n = len(sessions)
		sorted_sessions = sorted(self.__completed, key=lambda t: t[0])
		successes = [s for s in sessions if s.status in ['success', 'success-maintenance']]

		with file_lock:
			with open(f'{settings.runtime.OUTPUT_DIR}/results.json', 'w') as f:
				json.dump({
					'summary': {
						'n': n,
						'successes': len([s for s in sessions if s.status == 'success']),
						'maintenance': len([s for s in sessions if s.status == 'success-maintenance']),
						'failures': len([s for s in sessions if s.status == 'max-attempts-reached']),
						'initial_input_worked': len([s for s in sessions if len(s.attempts) == 1 and s.status == 'success']),
						'avg_attempts': sum(len(s.attempts) - 1 for s in sessions) / n if n > 0 else -1,
						'avg_duration': sum(s.duration for s in sessions) / n if n > 0 else -1,
						'avg_success_edit_distance': sum(s.edits[1] for s in successes) / len(successes) if successes else -1,
						'avg_success_constraints': sum(s.constraints['total'] for s in successes) / len(successes) if successes else -1,
					},
					'llm_token_usage': {
						'model': settings.agent.MODEL,
						'input_tokens': sum(s.token_usage.input_tokens for s in sessions),
						'output_tokens': sum(s.token_usage.output_tokens for s in sessions),
						'total_tokens': sum(s.token_usage.total_tokens for s in sessions),
					},
					'embedding_token_usage': {
						'model': settings.agent.EMBEDDING_MODEL if settings.runtime.USE_RAG else None,
						'build_log_tokens': sum(s.embedding_usage.build_log_tokens for s in sessions),
						'boot_log_tokens': sum(s.embedding_usage.boot_log_tokens for s in sessions),
						'total_tokens': sum(s.embedding_usage.total_tokens for s in sessions),
					},
					'time': {
						'avg_duration': sum(s.duration for s in sessions) / n if n > 0 else -1,
						'avg_duration_per_attempt': sum(s.duration for s in sessions) / sum(len(s.attempts) - 1 for s in sessions) if n > 0 and sum(len(s.attempts) - 1 for s in sessions) > 0 else -1,
					},
					'samples': [
						{
							'sample': idx + 1,
							'status': s.status,
							'attempts': len(s.attempts) - 1,
							'duration': s.duration,
							'edit_distance': s.edits[1] if s.edits else -1,
							'constraints': s.constraints,
							'llm_token_usage': s.token_usage.model_dump(),
							'embedding_token_usage': s.embedding_usage.model_dump(),
						} for idx, s in sorted_sessions
					]
				}, f, indent=4)

session_metrics = SessionMetrics()
experiment_metrics = ExperimentMetrics()
