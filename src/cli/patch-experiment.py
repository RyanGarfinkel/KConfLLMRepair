from src.experiment import experiment_metrics, session_metrics
from src.config import settings, log_settings
from src.utils import log, dispatcher
from src.kernel import worktree
from src.tools import koverage
from src.models import Sample
from typing import Callable
import subprocess
import shutil
import click
import json
import time
import sys
import os

def build_repair_cmd(sample: Sample, kernel_src: str, model: str, jobs: int, iterations: int, arch: str, img: str, min_coverage: float) -> list[str]:
	cmd = [
		sys.executable, '-u', '-m', 'src.cli.repair',
		'--output', sample.sample_dir,
		'--src', kernel_src,
		'--model', model,
		'--jobs', str(jobs),
		'--iterations', str(iterations),
		'--arch', arch,
		'--img', img,
		'--patch', sample.patch,
		'--min-coverage', str(min_coverage),
		'--config', sample.original_config,
	]

	return cmd

def load_samples(output_dir: str) -> list[Sample]:

	samples = []

	original_config = f'{output_dir}/patch-expriment-raw/original.config'
	
	for i in range(5):
		dir = f'{output_dir}/patch-expriment-raw/run_{i + 1}/commit_window_repair_output/'
		with os.scandir(dir) as entries:
			for entry in entries:
				if not entry.is_dir():
					continue

				patch = f'{dir}/{entry.name}/window_diff.patch'
				with open(f'{dir}/window_manifest.json', 'r') as f:
					data = json.load(f)

				start_commit = data.get('first_commit')
				end_commit = data.get('last_commit')
				modified_config = f'{dir}/{entry.name}/configuration_repair/largest_repaired.config'

				samples.append(Sample(
					original_config=original_config,
					modified_config=modified_config,
					patch=patch,
					seed=0,
					sample_dir=f'{dir}/{entry.name}',
					kernel_src='',
					kernel_version='',
					built=None,
					boot_status=None,
					start_commit=start_commit,
					start_commit_date=None,
					end_commit=end_commit,
					end_commit_date=None
				))

	return samples

def polish_raw(output_dir: str, samples: list[Sample]) -> list[Sample]:

	new_samples = []
	os.makedirs(f'{output_dir}/patch-experiment', exist_ok=True)

	for i, sample in enumerate(samples):
		dir = f'{output_dir}/patch-experiment/sample_{i + 1}'
		os.makedirs(dir, exist_ok=True)

		shutil.copy(sample.original_config, f'{dir}/original.config')
		shutil.copy(sample.modified_config, f'{dir}/base.config')
		shutil.copy(sample.patch, f'{dir}/changes.patch')

		new_samples.append(Sample(
			original_config=f'{dir}/original.config',
			modified_config=f'{dir}/base.config',
			patch=f'{dir}/changes.patch',
			sample_dir=dir,
			**sample.model_dump(exclude={'original_config', 'modified_config', 'patch', 'sample_dir'}),
		))

	return new_samples

def measure_original_coverage(kernel_src: str, sample_dir: str, config: str, patch: str) -> float | None:

	log_file = f'{sample_dir}/original_coverage/koverage.log'
	os.makedirs(os.path.dirname(log_file), exist_ok=True)

	status, coverage, _ = koverage.run(kernel_src, config, patch, log_file)
	if status != 'success':
		log.warning('Koverage failed while measuring original coverage.')

	return coverage

def make_task(s: Sample, model: str, jobs: int, iterations: int, arch: str, img: str, mode: str, constraints: str | None = None) -> Callable:

	sample_id = int(s.sample_dir.rstrip('/').split('_')[-1])

	def task():

		start = time.time()
		kernel_src = worktree.create(s.end_commit)

		original_coverage = measure_original_coverage(kernel_src, s.sample_dir, s.original_config, s.patch)

		cmd = build_repair_cmd(s, kernel_src=kernel_src, model=model, jobs=jobs, iterations=iterations, arch=arch, img=img, mode=mode, constraints=constraints, min_coverage=0.1) # <------

		log_file = f'{s.sample_dir}/terminal.log'

		os.makedirs(os.path.dirname(log_file), exist_ok=True)
		with open(log_file, 'w', buffering=1) as f:
			subprocess.run(cmd, stdout=f, stderr=f)

		duration = round(time.time() - start, 2)
		summary_path = f'{s.sample_dir}/agent_repair/summary.json'

		if not os.path.exists(summary_path):
			log.error(f'summary.json not found for {s.sample_dir}')
		else:
			experiment_metrics.record(sample_id, session_metrics.load(summary_path), duration, original_coverage)

		worktree.cleanup(kernel_src)

	return task

@click.command()
@click.option('--jobs', '-j', default=8, help='Number of parallel jobs for building kernels.')
@click.option('--threads', '-t', default=1, help='Number of samples to repair in parallel.')
@click.option('--model', '-m', default='gemini-3.1-pro-preview', help='LLM model to use for repair.')
@click.option('--iterations', '-i', default=20, help='Maximum repair iterations per sample.')
@click.option('--arch', '-a', default='x86_64', help='Target architecture (x86_64 or arm64).')
@click.option('--constraints', default=None, help='Path to a hard constraints file (OPTION to define, !OPTION to undefine).')
def main(jobs: int, threads: int, model: str, iterations: int, arch: str):

	output_dir = f'{settings.runtime.OUTPUT_DIR}/patch-experiment'
	settings.runtime.OUTPUT_DIR = output_dir
	settings.runtime.MAX_THREADS = threads
	settings.runtime.JOBS = jobs
	settings.agent.MODEL = model
	settings.agent.MAX_ITERATIONS = iterations
	settings.kernel.ARCH = arch

	img = os.environ.get('DEBIAN_IMG_ARM64') if arch == 'arm64' else os.environ.get('DEBIAN_IMG_AMD64', settings.kernel.DEBIAN_IMG)

	samples = load_samples(output_dir)
	if not samples:
		log.error(f'No samples found.')
		return

	log_settings()
	log.info(f'Found {len(samples)} patch samples for {arch}')

	samples = polish_raw(output_dir, samples)

	log.info('Transfered raw samples to patch-experiment dir.')

	valid = [s for s in samples if s.original_config and s.modified_config and s.patch]

	skipped = len(samples) - len(valid)
	if skipped:
		log.warning(f'Skipping {skipped} sample(s) with incomplete data.')

	labels = [f'sample {int(s.sample_dir.rstrip("/").split("_")[-1])}' for s in valid]

	dispatcher.run_callables(
		tasks=[make_task(s, model, jobs, iterations, arch, img) for s in valid],
		desc='Repairing samples',
		labels=labels,
	)

if __name__ == '__main__':
	main()
