from src.utils import log, dispatcher, file_lock
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

	def random(self, n: int, complete_callback: Callable[[int, Sample], None] | None = None) -> tuple[dict, list[Sample]]:

		summary, samples = self.__sample_random_configs(n)
		self.__save(summary, [])

		completed = []

		def process(i: int):

			sample = samples[i]

			kernel_src = worktree.create(sample.end_commit)
			kernel = Kernel(kernel_src)

			sample = Sample(
				**{**sample.model_dump(), 'kernel_src': kernel_src, 'kernel_version': kernel.version}
			)

			if os.path.exists(sample.sample_dir):
				shutil.rmtree(sample.sample_dir)

			os.makedirs(sample.sample_dir, exist_ok=True)

			if not kernel.make_rand_config(f'{sample.sample_dir}/.config', sample.seed):
				log.error(f'Failed to create random sample {i + 1}.')
				return

			sample.original_config = f'{sample.sample_dir}/.config'
			log.info(f'Sample {i + 1} created successfully.')

			completed.append(sample)
			self.__save(summary, completed)

			if complete_callback is not None:
				complete_callback(i, sample)

			if settings.runtime.CLEANUP:
				log.info(f'Cleaning up sample {i + 1} worktree...')
				worktree.cleanup(sample.kernel_src)

		tasks = [lambda idx=i: process(idx) for i in range(n)]
		dispatcher.run_tasks(tasks, desc='Generating samples')

		return summary, completed

	def __sample_random_configs(self, n: int) -> tuple[dict, list[Sample]]:

		kernel = Kernel(settings.kernel.KERNEL_SRC)

		summary = {
			'kernel_version': kernel.version,
			'end_commit': main_repo.head.commit.hexsha,
			'end_commit_date': main_repo.head.commit.committed_datetime.isoformat(),
			'n': n,
		}

		samples = [
			Sample(
				sample_dir=f'{settings.runtime.SAMPLE_DIR}/sample_{i}',
				seed=random.randint(1, 100000000),
				kernel_src='',
				kernel_version='',
				end_commit=main_repo.head.commit.hexsha,
				end_commit_date=main_repo.head.commit.committed_datetime.isoformat(),
			) for i in range(n)
		]

		return summary, samples

	# Patch

	def patch(self, n: int, since: str, complete_callback: Callable[[int, Sample], None] | None = None) -> tuple[dict, list[Sample]]:

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

			if os.path.exists(sample.sample_dir):
				shutil.rmtree(sample.sample_dir)

			os.makedirs(sample.sample_dir, exist_ok=True)

			if not self.__make_patch_sample(sample, kernel):
				log.error(f'Failed to create patch sample {i + 1}.')
				return

			log.success(f'Patch sample {i + 1} created successfully.')
			completed.append(sample)
			self.__save(summary, completed)

			if complete_callback is not None:
				complete_callback(i, sample)

			if settings.runtime.CLEANUP:
				log.info(f'Cleaning up sample {i + 1} worktree...')
				worktree.cleanup(sample.kernel_src)

		tasks = [lambda idx=i: process(idx) for i in range(n)]
		dispatcher.run_tasks(tasks, desc='Generating patch samples')

		return summary, completed

	def __sample_patch_commits(self, n: int, since: str) -> tuple[dict, list[Sample]]:

		log.info(f'Performing systematic random sampling of {n} commits from the repository...')

		all_commits = main_repo.git.rev_list('HEAD', f'--since={since}', '--no-merges').splitlines()
		total_commits = len(all_commits) - settings.runtime.COMMIT_WINDOW
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
			sample_dir=f'{settings.runtime.SAMPLE_DIR}/sample_{i}',
			kernel_src='',
			kernel_version='',
			start_commit=all_commits[start + i * k + settings.runtime.COMMIT_WINDOW],
			start_commit_date=main_repo.commit(all_commits[start + i * k + settings.runtime.COMMIT_WINDOW]).committed_datetime.isoformat(),
			end_commit=all_commits[start + i * k],
			end_commit_date=main_repo.commit(all_commits[start + i * k]).committed_datetime.isoformat(),
		) for i in range(n)]

		log.info(f'Sampled {n} commits, k is {k}, starting with commit {all_commits[start]}.')

		return summary, samples

	def __make_patch_sample(self, sample: Sample, kernel: Kernel) -> bool:

		# Base Config

		original_config = f'{sample.sample_dir}/base.config'

		log.info('Running syzkaller to generate base configuration...')
	
		if not syzkaller.run(kernel.src, original_config):
			log.error('Syzkaller failed to generate a base configuration.')
			return False
		
		log.success('Base configuration generated successfully.')
		log.info('Verifying base configuration bootability...')

		if not kernel.load_config(original_config):
			log.error('Failed to load base configuration.')
			return False
		
		if kernel.build(f'{sample.sample_dir}/build.log') and kernel.boot(f'{sample.sample_dir}/boot.log') == 'yes':
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
		
		if not kernel.load_config(original_config):
			log.error('Failed to load original configuration for patch sample.')
			return False
		
		if not kernel.run_klocalizer(f'{sample.sample_dir}/klocalizer.log', patch=patch_path) == 'success':
			log.error('KLocalizer failed for patch sample.')
			return False
		
		modified_config = f'{sample.sample_dir}/modified.config'
		shutil.copyfile(f'{kernel.src}/.config', modified_config)
		sample.modified_config = modified_config

		return True

	def __save(self, summary: dict, completed_samples: list[Sample]):

		with file_lock:
			with open(f'{settings.runtime.SAMPLE_DIR}/sampling.json', 'w') as f:
				json.dump({
					'summary': summary,
					'samples': [s.model_dump() for s in completed_samples]
				}, f, indent=4)

sampler = Sampler()
