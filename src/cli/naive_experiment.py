from src.config import settings, log_settings
from src.utils import log, dispatcher
from src.utils.lock import file_lock
from src.kernel import worktree
from src.models import Sample
from typing import Callable
import subprocess
import click
import json
import time
import sys
import os

_results: list[tuple[int, dict]] = []

def build_naive_cmd(sample: Sample, kernel_src: str, model: str, jobs: int, arch: str, img: str | None) -> list[str]:
	cmd = [
		sys.executable, '-u', '-m', 'src.cli.naive',
		'--output', sample.sample_dir,
		'--src', kernel_src,
		'--model', model,
		'--jobs', str(jobs),
		'--arch', arch,
		'--config', sample.original_config,
		'--build-log', f'{sample.sample_dir}/build.log',
		'--boot-log', f'{sample.sample_dir}/boot.log',
	]

	if img is not None:
		cmd += ['--img', img]

	return cmd

def load_samples(output_dir: str) -> list[Sample]:
	with open(f'{output_dir}/sampling.json', 'r') as f:
		data = json.load(f)

	return [Sample(**s) for s in data.get('samples', [])]

def _record(sample_id: int, result: dict):
	with file_lock:
		_results.append((sample_id, result))

		entries = [d for _, d in _results]
		n = len(entries)
		sorted_entries = sorted(_results, key=lambda t: t[0])
		successes = [d for d in entries if d['status'] in ('success', 'success-maintenance')]

		with open(f'{settings.runtime.OUTPUT_DIR}/results.json', 'w', encoding='utf-8') as f:
			json.dump({
				'summary': {
					'n': n,
					'successes': len([d for d in entries if d['status'] == 'success']),
					'maintenance': len([d for d in entries if d['status'] == 'success-maintenance']),
					'build_failures': len([d for d in entries if d['status'] == 'build-failure']),
					'boot_failures': len([d for d in entries if d['status'] == 'boot-failure']),
					'truncated': len([d for d in entries if d.get('truncated')]),
					'avg_duration': sum(d['duration'] for d in entries) / n,
				},
				'llm_token_usage': {
					'model': settings.agent.MODEL,
					'total': {
						'input_tokens': sum(d['token_usage']['input_tokens'] for d in entries),
						'output_tokens': sum(d['token_usage']['output_tokens'] for d in entries),
						'total_tokens': sum(d['token_usage']['total_tokens'] for d in entries),
					},
					'avg_per_repair': {
						'input_tokens': sum(d['token_usage']['input_tokens'] for d in entries) / n,
						'output_tokens': sum(d['token_usage']['output_tokens'] for d in entries) / n,
						'total_tokens': sum(d['token_usage']['total_tokens'] for d in entries) / n,
					},
				},
				'time': {
					'avg_llm': sum(d['time']['llm'] for d in entries) / n,
					'avg_build': sum(d['time']['build'] for d in entries) / n,
					'avg_boot': sum(d['time']['boot'] for d in entries if d['status'] != 'build-failure') / max(len([d for d in entries if d['status'] != 'build-failure']), 1),
					'avg_duration': sum(d['duration'] for d in entries) / n,
					'avg_success_duration': sum(d['duration'] for d in successes) / len(successes) if successes else -1,
				},
				'samples': [
					{
						'sample': idx + 1,
						'status': d['status'],
						'boot_status': d.get('boot_status'),
						'build_error': d.get('build_error'),
						'truncated': d.get('truncated'),
						'finish_reason': d.get('finish_reason'),
						'original_lines': d.get('original_lines'),
						'repaired_lines': d.get('repaired_lines'),
						'token_usage': d['token_usage'],
						'time': d['time'],
						'duration': d['duration'],
					} for idx, d in sorted_entries
				],
			}, f, indent=4)

def make_task(s: Sample, model: str, jobs: int, arch: str, img: str | None) -> Callable:

	sample_id = int(s.sample_dir.rstrip('/').split('_')[-1])

	def task():
		start = time.time()
		kernel_src = worktree.create(s.end_commit)
		cmd = build_naive_cmd(s, kernel_src=kernel_src, model=model, jobs=jobs, arch=arch, img=img)

		log_file = f'{s.sample_dir}/terminal.log'
		os.makedirs(os.path.dirname(log_file), exist_ok=True)
		with open(log_file, 'w', buffering=1) as f:
			subprocess.run(cmd, stdout=f, stderr=f)

		duration = round(time.time() - start, 2)
		worktree.cleanup(kernel_src)

		result_path = f'{s.sample_dir}/llm-repair/result.json'
		if not os.path.exists(result_path):
			log.error(f'result.json not found for {s.sample_dir}')
			return

		with open(result_path) as f:
			result = json.load(f)

		result['duration'] = duration
		_record(sample_id, result)

	return task

@click.command()
@click.option('--jobs', '-j', default=8, help='Number of parallel jobs for building kernels.')
@click.option('--threads', '-t', default=1, help='Number of samples to repair in parallel.')
@click.option('--model', '-m', default='gemini-3.1-pro-preview', help='LLM model to use.')
@click.option('--arch', '-a', default='x86_64', help='Target architecture (x86_64 or arm64).')
def main(jobs: int, threads: int, model: str, arch: str):

	output_dir = f'{settings.runtime.OUTPUT_DIR}/{arch}'
	settings.runtime.OUTPUT_DIR = output_dir
	settings.runtime.MAX_THREADS = threads
	settings.runtime.JOBS = jobs
	settings.agent.MODEL = model
	settings.kernel.ARCH = arch

	img = os.environ.get('DEBIAN_IMG_ARM64') if arch == 'arm64' else os.environ.get('DEBIAN_IMG_AMD64', settings.kernel.DEBIAN_IMG)

	sampling_json = f'{output_dir}/sampling.json'
	if not os.path.exists(sampling_json):
		log.error(f'No sampling.json found at {sampling_json}')
		return

	samples = load_samples(output_dir)
	if not samples:
		log.error(f'No samples found in {sampling_json}')
		return

	log_settings()
	log.info(f'Found {len(samples)} samples for {arch}')

	valid = [s for s in samples if s.original_config]
	skipped = len(samples) - len(valid)
	if skipped:
		log.warning(f'Skipping {skipped} sample(s) with incomplete data.')

	labels = [f'sample {int(s.sample_dir.rstrip("/").split("_")[-1])}' for s in valid]

	dispatcher.run_callables(
		tasks=[make_task(s, model, jobs, arch, img) for s in valid],
		desc='Running naive repair on samples',
		labels=labels,
	)

if __name__ == '__main__':
	main()
