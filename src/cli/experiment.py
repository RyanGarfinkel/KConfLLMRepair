from src.experiment import experiment_metrics, session_metrics
from src.config import settings, log_settings
from src.utils import log, dispatcher
from src.kernel import worktree
from src.models import Sample
from typing import Callable
import subprocess
import click
import json
import time
import sys
import os

def build_repair_cmd(sample: Sample, kernel_src: str, model: str, jobs: int, iterations: int, arch: str, img: str, mode: str, constraints: str | None = None) -> list[str]:
	cmd = [
		sys.executable, '-u', '-m', 'src.cli.repair',
		'--output', sample.sample_dir,
		'--src', kernel_src,
		'--model', model,
		'--jobs', str(jobs),
		'--iterations', str(iterations),
		'--arch', arch,
		'--img', img,
	]

	if mode == 'patch':
		cmd += ['--original', sample.original_config, '--modified', sample.modified_config, '--patch', sample.patch]
	else:
		cmd += ['--config', sample.original_config]

	if constraints is not None:
		cmd += ['--constraints', constraints]
	
	return cmd

def load_samples(output_dir: str) -> list[Sample]:
	with open(f'{output_dir}/sampling.json', 'r') as f:
		data = json.load(f)
	
	return [Sample(**s) for s in data.get('samples', [])]

def make_task(s: Sample, model: str, jobs: int, iterations: int, arch: str, img: str, mode: str, constraints: str | None = None) -> Callable:
	
	sample_id = int(s.sample_dir.rstrip('/').split('_')[-1])

	def task():

		start = time.time()
		kernel_src = worktree.create(s.end_commit)
		cmd = build_repair_cmd(s, kernel_src=kernel_src, model=model, jobs=jobs, iterations=iterations, arch=arch, img=img, mode=mode, constraints=constraints)
		
		log_file = f'{s.sample_dir}/terminal.log'
		
		os.makedirs(os.path.dirname(log_file), exist_ok=True)
		with open(log_file, 'w', buffering=1) as f:
			subprocess.run(cmd, stdout=f, stderr=f)
		
		duration = round(time.time() - start, 2)
		summary_path = f'{s.sample_dir}/agent_repair/summary.json'

		if not os.path.exists(summary_path):
			log.error(f'summary.json not found for {s.sample_dir}')
		else:
			experiment_metrics.record(sample_id, session_metrics.load(summary_path), duration)
		
		worktree.cleanup(kernel_src)
		
	return task

@click.command()
@click.option('--jobs', '-j', default=8, help='Number of parallel jobs for building kernels.')
@click.option('--threads', '-t', default=1, help='Number of samples to repair in parallel.')
@click.option('--model', '-m', default='gemini-3.1-pro-preview', help='LLM model to use for repair.')
@click.option('--iterations', '-i', default=20, help='Maximum repair iterations per sample.')
@click.option('--arch', '-a', default='x86_64', help='Target architecture (x86_64 or arm64).')
@click.option('--patch', 'mode', flag_value='patch', help='Use patch-based samples.')
@click.option('--random', 'mode', flag_value='random', default=True, help='Use random config samples (default).')
@click.option('--constraints', default=None, help='Path to a hard constraints file (OPTION to define, !OPTION to undefine).')
def main(jobs: int, threads: int, model: str, iterations: int, arch: str, mode: str, constraints: str | None):

	output_dir = f'{settings.runtime.OUTPUT_DIR}/{arch}'
	settings.runtime.OUTPUT_DIR = output_dir
	settings.runtime.MAX_THREADS = threads
	settings.runtime.JOBS = jobs
	settings.agent.MODEL = model
	settings.agent.MAX_ITERATIONS = iterations
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
	log.info(f'Found {len(samples)} {mode} samples for {arch}')

	if mode == 'patch':
		valid = [s for s in samples if s.original_config and s.modified_config and s.patch]
	else:
		valid = [s for s in samples if s.original_config]

	skipped = len(samples) - len(valid)
	if skipped:
		log.warning(f'Skipping {skipped} sample(s) with incomplete data.')

	dispatcher.run_callables(
		tasks=[make_task(s, model, jobs, iterations, arch, img, mode, constraints) for s in valid],
		desc='Repairing samples',
	)

if __name__ == '__main__':
	main()
