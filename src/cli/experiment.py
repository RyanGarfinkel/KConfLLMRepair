from src.experiment import experiment_metrics, session_metrics
from src.models import Sample
from src.utils import log, dispatcher
from src.config import settings
import click
import json
import sys
import os

def build_repair_cmd(sample: Sample, model: str, jobs: int, iterations: int, arch: str, img: str, mode: str) -> list[str]:
	cmd = [
		sys.executable, '-m', 'src.cli.repair',
		'--output', sample.sample_dir,
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
	return cmd

def load_samples(output_dir: str) -> list[Sample]:
	with open(f'{output_dir}/sampling.json', 'r') as f:
		data = json.load(f)
	return [Sample(**s) for s in data.get('samples', [])]

def on_sample_complete(i: int, sample: Sample, duration: float):
	summary_path = f'{sample.sample_dir}/summary.json'
	if not os.path.exists(summary_path):
		log.error(f'summary.json not found for {sample.sample_dir}')
		return
	data = session_metrics.load(summary_path)
	experiment_metrics.record(i, data, duration)

@click.command()
@click.option('--jobs', '-j', default=8, help='Number of parallel jobs for building kernels.')
@click.option('--threads', '-t', default=1, help='Number of samples to repair in parallel.')
@click.option('--model', '-m', default='gemini-3.1-pro-preview', help='LLM model to use for repair.')
@click.option('--iterations', '-i', default=20, help='Maximum repair iterations per sample.')
@click.option('--arch', '-a', default='x86_64', help='Target architecture (x86_64 or arm64).')
@click.option('--patch', 'mode', flag_value='patch', help='Use patch-based samples.')
@click.option('--random', 'mode', flag_value='random', default=True, help='Use random config samples (default).')
def main(jobs: int, threads: int, model: str, iterations: int, arch: str, mode: str):

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

	log.info(f'Found {len(samples)} {mode} samples for {arch}')

	if mode == 'patch':
		valid = [s for s in samples if s.original_config and s.modified_config and s.patch]
	else:
		valid = [s for s in samples if s.original_config]

	skipped = len(samples) - len(valid)
	if skipped:
		log.warning(f'Skipping {skipped} sample(s) with incomplete data.')

	commands = [
		build_repair_cmd(s, model=model, jobs=jobs, iterations=iterations, arch=arch, img=img, mode=mode)
		for s in valid
	]

	dispatcher.run_repairs(
		commands=commands,
		log_path=lambda i: f'{valid[i].sample_dir}/terminal.log',
		on_complete=lambda i, duration: on_sample_complete(i, valid[i], duration),
	)

if __name__ == '__main__':
	main()
