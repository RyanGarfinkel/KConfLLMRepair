from src.utils import log, dispatcher, file_lock, seed_lock
from singleton_decorator import singleton
from src.kernel import worktree
from src.config import settings
from src.tools import syzkaller
from src.models import Sample
from typing import Callable
from src.core import Kernel
import random
import shutil
import json
import os

main_repo = worktree.main_repo

@singleton
class Sampler:

	# Random

	def random(self, n: int, hard_define: set[str] = set(), hard_undefine: set[str] = set(), complete_callback: Callable[[int, Sample], None] | None = None) -> tuple[dict, list[Sample]]:

		summary, samples = self.__sample_random_configs(n)
		self.__save(summary, [])

		completed = []
		used_seeds = {s.seed for s in samples}

		def next_seed() -> int:
			with seed_lock:
				while True:
					s = random.randint(1, 100000000)
					if s not in used_seeds:
						used_seeds.add(s)
						return s

		def process(i: int):

			sample = samples[i]

			kernel_src = worktree.create(sample.end_commit)
			kernel = Kernel(kernel_src)

			sample = Sample(
				**{**sample.model_dump(), 'kernel_src': kernel_src, 'kernel_version': kernel.version}
			)

			try:
				confirmed = False

				for attempt in range(1, 6):

					if attempt > 1:
						sample.seed = next_seed()
						log.info(f'Sample {i + 1} booted — retrying with new seed (attempt {attempt}).')

					if os.path.exists(sample.sample_dir):
						shutil.rmtree(sample.sample_dir)

					os.makedirs(sample.sample_dir, exist_ok=True)

					if not kernel.make_rand_config(f'{sample.sample_dir}/.config', sample.seed):
						log.error(f'Failed to create random config for sample {i + 1}.')
						return

					sample.original_config = f'{sample.sample_dir}/.config'

					if hard_define or hard_undefine:
						result = kernel.run_klocalizer(sample.sample_dir, sample.original_config, define=list(hard_define), undefine=list(hard_undefine))
						if result.status != 'success':
							log.warning(f'KLocalizer failed to apply constraints for sample {i + 1}. Proceeding with unconstrained config.')
						else:
							shutil.copyfile(f'{kernel.src}/.config', sample.original_config)

					build_result = kernel.build(sample.sample_dir, sample.original_config)
					sample.built = build_result.ok

					if not build_result.ok:
						log.info(f'Sample {i + 1} confirmed non-bootable (build failed).')
						confirmed = True
						break

					boot_result = kernel.boot(sample.sample_dir)
					sample.boot_status = boot_result.status

					if boot_result.status != 'yes':
						log.info(f'Sample {i + 1} confirmed non-bootable.')
						confirmed = True
						break

				if not confirmed:
					log.error(f'Sample {i + 1} failed to produce a non-bootable config after 5 attempts.')
					return

				log.success(f'Sample {i + 1} created successfully.')
				completed.append(sample)
				self.__save(summary, completed)

				if complete_callback is not None:
					complete_callback(i, sample)

			finally:
				if settings.runtime.CLEANUP:
					log.info(f'Cleaning up sample {i + 1} worktree...')
					worktree.cleanup(sample.kernel_src)

		tasks = [lambda idx=i: process(idx) for i in range(n)]
		dispatcher.run_callables(tasks)

		return summary, completed

	def __sample_random_configs(self, n: int) -> tuple[dict, list[Sample]]:

		kernel = Kernel(settings.kernel.KERNEL_SRC)

		summary = {
			'kernel_version': kernel.version,
			'end_commit': main_repo.head.commit.hexsha,
			'end_commit_date': main_repo.head.commit.committed_datetime.isoformat(),
			'n': n,
		}

		seeds = random.sample(range(1, 100000001), n)

		samples = [
			Sample(
				sample_dir=f'{settings.runtime.OUTPUT_DIR}/sample_{i}',
				seed=seeds[i],
				kernel_src='',
				kernel_version='',
				end_commit=main_repo.head.commit.hexsha,
				end_commit_date=main_repo.head.commit.committed_datetime.isoformat(),
			) for i in range(n)
		]

		return summary, samples

	# Patch

	def patch(self, n: int, since: str, hard_define: set[str] = set(), hard_undefine: set[str] = set(), complete_callback: Callable[[int, Sample], None] | None = None) -> tuple[dict, list[Sample]]:

		summary, samples = self.__sample_patch_commits(n, since)
		self.__save(summary, [])

		completed = []

		def process(i: int):
			sample = samples[i]

			kernel_src = worktree.create(sample.end_commit)
			kernel = Kernel(kernel_src)

			sample = Sample(
				**{**sample.model_dump(), 'kernel_src': kernel_src, 'kernel_version': kernel.version}
			)

			try:
				if os.path.exists(sample.sample_dir):
					shutil.rmtree(sample.sample_dir)

				os.makedirs(sample.sample_dir, exist_ok=True)

				if not self.__make_patch_sample(sample, kernel, hard_define, hard_undefine):
					log.error(f'Failed to create patch sample {i + 1}.')
					return

				log.success(f'Patch sample {i + 1} created successfully.')
				completed.append(sample)
				self.__save(summary, completed)

				if complete_callback is not None:
					complete_callback(i, sample)

			finally:
				if settings.runtime.CLEANUP:
					log.info(f'Cleaning up sample {i + 1} worktree...')
					worktree.cleanup(sample.kernel_src)

		tasks = [lambda idx=i: process(idx) for i in range(n)]
		dispatcher.run_callables(tasks)

		return summary, completed

	def __sample_patch_commits(self, n: int, since: str) -> tuple[dict, list[Sample]]:

		log.info(f'Performing systematic random sampling of {n} commits from the repository...')

		all_commits = main_repo.git.rev_list('HEAD', f'--since={since}', '--no-merges').splitlines()
		total_commits = len(all_commits) - settings.runtime.COMMIT_WINDOW

		if total_commits < n:
			raise ValueError(f'Not enough commits ({total_commits}) for {n} samples with COMMIT_WINDOW={settings.runtime.COMMIT_WINDOW}.')

		k = total_commits // n
		start = random.randint(0, k)

		summary = {
			'start': start,
			'k': k,
			'n': n,
			'total_commits': total_commits,
			'last_commit': {
				'hexsha': all_commits[0],
				'date': main_repo.commit(all_commits[0]).committed_datetime.isoformat()
			},
			'earliest_commit': {
				'hexsha': all_commits[-1],
				'date': main_repo.commit(all_commits[-1]).committed_datetime.isoformat()
			},
		}

		samples = [Sample(
			original_config='',
			sample_dir=f'{settings.runtime.OUTPUT_DIR}/sample_{i}',
			kernel_src='',
			kernel_version='',
			start_commit=all_commits[start + i * k + settings.runtime.COMMIT_WINDOW],
			start_commit_date=main_repo.commit(all_commits[start + i * k + settings.runtime.COMMIT_WINDOW]).committed_datetime.isoformat(),
			end_commit=all_commits[start + i * k],
			end_commit_date=main_repo.commit(all_commits[start + i * k]).committed_datetime.isoformat(),
		) for i in range(n)]

		log.info(f'Sampled {n} commits, k is {k}, starting with commit {all_commits[start]}.')

		return summary, samples

	def __make_patch_sample(self, sample: Sample, kernel: Kernel, hard_define: set[str] = set(), hard_undefine: set[str] = set()) -> bool:

		# Base Config

		original_config = f'{sample.sample_dir}/base.config'

		log.info('Running syzkaller to generate base configuration...')
	
		if not syzkaller.run(kernel.src, original_config):
			log.error('Syzkaller failed to generate a base configuration.')
			return False
		
		log.success('Base configuration generated successfully.')
		log.info('Verifying base configuration bootability...')

		if kernel.build(sample.sample_dir, original_config).ok and kernel.boot(sample.sample_dir).status == 'yes':
			log.success('Base configuration is valid and bootable.')
			sample.original_config = original_config
		else:
			log.error('Base configuration failed to boot.')
			return False
		
		# Modified Config

		patch_path = f'{sample.sample_dir}/changes.patch'
		if not kernel.make_patch(patch_path):
			log.error('Failed to create patch for sample.')
			return False

		sample.patch = patch_path
		
		if kernel.run_klocalizer(sample.sample_dir, original_config, define=list(hard_define), undefine=list(hard_undefine), patch=patch_path).status != 'success':
			log.error('KLocalizer failed for patch sample.')
			return False
		
		modified_config = f'{sample.sample_dir}/modified.config'
		shutil.copyfile(f'{kernel.src}/.config', modified_config)
		sample.modified_config = modified_config

		return True

	def read_samples(self, n: int) -> list[Sample]:
		with open(f'{settings.runtime.OUTPUT_DIR}/sampling.json', 'r') as f:
			data = json.load(f)
		return [Sample(**s) for s in data.get('samples', [])][:n]

	def __save(self, summary: dict, completed_samples: list[Sample]):

		with file_lock:
			os.makedirs(settings.runtime.OUTPUT_DIR, exist_ok=True)
			with open(f'{settings.runtime.OUTPUT_DIR}/sampling.json', 'w') as f:
				json.dump({
					'summary': {
						**summary,
						'completed': len(completed_samples),
						'build_failed': sum(1 for s in completed_samples if s.built is False),
						'boot_failed': sum(1 for s in completed_samples if s.built and s.boot_status not in ('yes', None)),
					},
					'samples': [s.model_dump() for s in completed_samples]
				}, f, indent=4)

sampler = Sampler()
