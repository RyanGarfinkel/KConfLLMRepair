from langchain_core.messages import HumanMessage, SystemMessage
from src.config import settings, log_settings
from src.models import BuildResult, BootResult
from src.core.kernel import Kernel
from src.agent import model
from src.utils import log
import click
import json
import time
import re
import os

SYSTEM_PROMPT = """
	ROLE: You are an expert Linux kernel configuration agent tasked with repairing a non-booting kernel configuration.
	You specialize in reading and understanding build and boot logs, and are knowledgeable about how different configuration
	options impact the build and boot process.

	RESPONSE FORMAT: Respond with the content in a new, modified .config file only.
"""

TRUNCATED_REASONS = {'MAX_TOKENS', 'length', 'max_tokens', 'MAX_LENGTH'}

def _read(path: str | None) -> str:
	if path is None or not os.path.exists(path):
		return 'Not available'

	with open(path, 'r', errors='replace') as f:
		return f.read()

def _extract_config(text: str) -> str:
	match = re.search(r'```[^\n]*\n(.*?)```', text, re.DOTALL)
	if match:
		return match.group(1).strip()

	return text.strip()

def naive_repair(config: str, build_log: str, boot_log: str, output_dir: str) -> tuple[str, dict]:

	os.makedirs(output_dir, exist_ok=True)

	config_content = _read(config)
	build_content = _read(build_log)
	boot_content = _read(boot_log)

	user_message = f"""
	INSTRUCTIONS:
	Review the broken config, build log, and boot log below. Identify which configuration options are causing the failure
	and produce a repaired .config that will successfully build and boot. Respond with ONLY the complete repaired .config
	file content — no explanation, no markdown, no code fences.

	BROKEN CONFIG
	{config_content}

	BUILD LOG
	{build_content}

	BOOT LOG
	{boot_content}
"""

	log.info('Starting LLM repair...')

	llm = model.get_llm()
	llm_start = time.time()
	response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_message)])
	llm_time = round(time.time() - llm_start, 2)

	finish_reason = (response.response_metadata or {}).get('finish_reason', 'unknown')
	truncated = finish_reason in TRUNCATED_REASONS

	usage = response.usage_metadata or {}
	token_usage = {
		'input_tokens': usage.get('input_tokens', 0),
		'output_tokens': usage.get('output_tokens', 0),
		'total_tokens': usage.get('total_tokens', 0),
	}
	log.info(f'LLM call complete — {token_usage["input_tokens"]} in / {token_usage["output_tokens"]} out tokens (finish_reason={finish_reason})')
	with open(f'{output_dir}/token_usage.json', 'w') as f:
		json.dump(token_usage, f, indent=2)

	with open(f'{output_dir}/raw-llm-response.json', 'w') as f:
		def default(o):
			if hasattr(o, 'model_dump'):
				return o.model_dump()
			if hasattr(o, 'dict'):
				return o.dict()
			return str(o)

		json.dump(response, f, indent=4, default=default)

	content = response.content if isinstance(response.content, str) else ''.join(p.get('text', '') if isinstance(p, dict) else str(p) for p in response.content)
	repaired_config = _extract_config(content)
	repaired_path = f'{output_dir}/modified.config'
	with open(repaired_path, 'w') as f:
		f.write(repaired_config)

	log.info(f'Repaired config written to {repaired_path}')

	return repaired_path, {
		'llm_time': llm_time,
		'finish_reason': finish_reason,
		'truncated': truncated,
		'original_lines': len(config_content.splitlines()),
		'repaired_lines': len(repaired_config.splitlines()),
		'token_usage': token_usage,
	}

def _verify(kernel: Kernel, config: str, output_dir: str) -> tuple[BuildResult, BootResult | None]:

	build_result = kernel.build(output_dir, config)
	log.info(f'Build time: {build_result.build_time:.1f}s')
	if not build_result.ok:
		log.error('Repaired config failed to build.')
		return build_result, None

	boot_result = kernel.boot(output_dir)
	if boot_result.status == 'yes':
		log.success('Repaired config boots successfully!')
	elif boot_result.status == 'maintenance':
		log.info('Repaired config boots into maintenance mode.')
	else:
		log.error('Repaired config failed to boot.')

	return build_result, boot_result

@click.command()
@click.option('--config', required=True, help='Path to the broken .config file.')
@click.option('--build-log', required=True, help='Path to the build log.')
@click.option('--boot-log', required=True, help='Path to the boot log.')
@click.option('--output', '-o', default=os.getcwd(), help='Directory to write output. Defaults to current working directory.')
@click.option('--src', default=None, help='Path to kernel source. Defaults to $KERNEL_SRC.')
@click.option('--model', '-m', default='gemini-3.1-pro-preview', help='LLM model to use.')
@click.option('--jobs', '-j', default=8, help='Parallel jobs for kernel build.')
@click.option('--arch', '-a', default=None, help='Target architecture (e.g. x86_64, arm64).')
@click.option('--img', default=None, help='Path to Debian root filesystem image for QEMU.')
def main(config: str, build_log: str, boot_log: str, output: str, src: str | None, model: str, jobs: int, arch: str | None, img: str | None):

	settings.runtime.OUTPUT_DIR = output
	settings.runtime.JOBS = jobs
	settings.agent.MODEL = model

	if arch is not None:
		settings.kernel.ARCH = arch

	if img is not None:
		settings.kernel.DEBIAN_IMG = img

	if src is None:
		src = settings.kernel.KERNEL_SRC
	elif not os.path.exists(src):
		raise ValueError(f'Kernel source path does not exist: {src}')

	src = os.path.abspath(src)
	log_settings()

	kernel = Kernel(src)
	output_dir = f'{os.path.abspath(output)}/llm-repair'

	total_start = time.time()
	repaired_path, llm_info = naive_repair(config, build_log, boot_log, output_dir)
	build_result, boot_result = _verify(kernel, repaired_path, output_dir)
	duration = round(time.time() - total_start, 2)

	if not build_result.ok:
		status = 'build-failure'
	elif boot_result is None:
		status = 'build-failure'
	elif boot_result.status == 'yes':
		status = 'success'
	elif boot_result.status == 'maintenance':
		status = 'success-maintenance'
	else:
		status = 'boot-failure'

	result = {
		'status': status,
		'boot_status': boot_result.status if boot_result else None,
		'build_error': build_result.summary if not build_result.ok else None,
		'truncated': llm_info['truncated'],
		'finish_reason': llm_info['finish_reason'],
		'original_lines': llm_info['original_lines'],
		'repaired_lines': llm_info['repaired_lines'],
		'token_usage': llm_info['token_usage'],
		'time': {
			'llm': llm_info['llm_time'],
			'build': build_result.build_time,
			'boot': boot_result.boot_time if boot_result else 0.0,
			'duration': duration,
		},
	}

	with open(f'{output_dir}/result.json', 'w') as f:
		json.dump(result, f, indent=2)

	log.info(f'Total time: {duration:.1f}s | LLM: {llm_info["llm_time"]:.1f}s | Build: {build_result.build_time:.1f}s')

if __name__ == '__main__':
	main()
