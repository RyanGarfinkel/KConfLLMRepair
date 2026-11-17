from collections import defaultdict
import glob
import os
import re

TOKEN = re.compile(r'\|\||&&|!=|<=|>=|[!()=<>]|"[^"]*"|[A-Za-z0-9_.\-]+')
NUMBER = re.compile(r'-?(0x[0-9a-fA-F]+|\d+)')
TYPES = ('bool', 'tristate', 'string', 'int', 'hex')
RELATIVE_SOURCES = ('rsource', 'orsource')
SOURCES = ('source', 'osource') + RELATIVE_SOURCES
TRISTATE = {'y': 2, 'm': 1}

class Kconfig:

	def __init__(self, src: str, srcarch: str):

		self.src = src
		self.srcarch = srcarch
		self.definitions = defaultdict(list)
		self.selectors = defaultdict(list)

		self.__parse(os.path.join(src, 'Kconfig'), [])

	def exists(self, name: str) -> bool:
		return name in self.definitions

	def has_prompt(self, name: str) -> bool:
		return any(definition['prompt'] for definition in self.definitions[name])

	def dependencies_met(self, name: str, config: dict) -> bool:
		return any(all(evaluate(expr, config) for expr in definition['depends']) for definition in self.definitions[name])

	def active_selectors(self, name: str, config: dict) -> list[str]:
		return [selector for selector, cond in self.selectors[name] if evaluate(selector, config) and (cond is None or evaluate(cond, config))]

	def __parse(self, path: str, stack: list):

		with open(path, encoding='utf-8', errors='replace') as f:
			lines = join_continuations(f.read().split('\n'))

		current = None
		name = None
		help_indent = None

		for raw in lines:

			indent = len(raw.expandtabs()) - len(raw.expandtabs().lstrip())

			if help_indent is not None:
				if not raw.strip() or indent > help_indent:
					continue
				help_indent = None

			line = strip_comment(raw).strip()
			if not line:
				continue

			keyword, _, rest = line.partition(' ')
			keyword = keyword.strip()
			rest = rest.strip()

			if keyword in ('help', '---help---'):
				help_indent = indent
			elif keyword in ('config', 'menuconfig'):
				name = rest
				current = {'depends': [expr for _, expr in stack if expr], 'prompt': False}
				self.definitions[name].append(current)
			elif keyword in ('menu', 'choice'):
				stack.append([keyword, None])
				current = stack[-1]
			elif keyword == 'if':
				stack.append(['if', rest])
				current = None
			elif keyword in ('endmenu', 'endchoice', 'endif'):
				stack.pop()
				current = None
			elif keyword in SOURCES:
				target = rest.strip('"').replace('$(SRCARCH)', self.srcarch)
				base = os.path.dirname(path) if keyword in RELATIVE_SOURCES else self.src
				for source in sorted(glob.glob(os.path.join(base, target))):
					self.__parse(source, stack)
				current = None
			elif keyword in ('comment', 'mainmenu'):
				current = None
			elif keyword == 'depends' and current is not None:
				expr = rest.removeprefix('on').strip()
				if isinstance(current, list):
					current[1] = f'({current[1]}) && ({expr})' if current[1] else expr
				else:
					current['depends'].append(expr)
			elif isinstance(current, dict):
				if keyword == 'prompt' or (keyword in TYPES and rest.startswith('"')):
					current['prompt'] = True
				elif keyword == 'select':
					target, _, cond = rest.partition(' if ')
					self.selectors[target.strip()].append((name, cond.strip() or None))

def join_continuations(lines: list[str]) -> list[str]:

	joined = []
	buffer = ''

	for line in lines:
		if line.endswith('\\'):
			buffer += line[:-1] + ' '
			continue
		joined.append(buffer + line)
		buffer = ''

	return joined

def strip_comment(line: str) -> str:

	quoted = False

	for i, char in enumerate(line):
		if char == '"':
			quoted = not quoted
		elif char == '#' and not quoted:
			return line[:i]

	return line

def strip_macros(expr: str) -> str:

	output = []
	depth = 0
	i = 0

	while i < len(expr):
		if expr.startswith('$(', i):
			if depth == 0:
				output.append('y')
			depth += 1
			i += 2
			continue

		if depth:
			depth += {'(': 1, ')': -1}.get(expr[i], 0)
		else:
			output.append(expr[i])
		i += 1

	return ''.join(output)

def evaluate(expr: str, config: dict) -> int:

	tokens = TOKEN.findall(strip_macros(expr))
	if not tokens:
		return 2

	value, _ = parse_or(tokens, 0, config)
	return value

def parse_or(tokens: list[str], i: int, config: dict) -> tuple[int, int]:

	value, i = parse_and(tokens, i, config)

	while i < len(tokens) and tokens[i] == '||':
		right, i = parse_and(tokens, i + 1, config)
		value = max(value, right)

	return value, i

def parse_and(tokens: list[str], i: int, config: dict) -> tuple[int, int]:

	value, i = parse_unary(tokens, i, config)

	while i < len(tokens) and tokens[i] == '&&':
		right, i = parse_unary(tokens, i + 1, config)
		value = min(value, right)

	return value, i

def parse_unary(tokens: list[str], i: int, config: dict) -> tuple[int, int]:

	if tokens[i] == '!':
		value, i = parse_unary(tokens, i + 1, config)
		return 2 - value, i

	if tokens[i] == '(':
		value, i = parse_or(tokens, i + 1, config)
		return value, i + 1

	left = symbol_value(tokens[i], config)
	i += 1

	if i < len(tokens) and tokens[i] in ('=', '!=', '<', '>', '<=', '>='):
		right = symbol_value(tokens[i + 1], config)
		return (2 if compare(left, tokens[i], right) else 0), i + 2

	return TRISTATE.get(left, 0), i

def symbol_value(token: str, config: dict) -> str:

	if token.startswith('"'):
		return token.strip('"')

	if token in ('y', 'm', 'n'):
		return token

	key = f'CONFIG_{token}'
	if key in config:
		return config[key].strip('"')

	return token if NUMBER.fullmatch(token) else 'n'

def compare(left: str, op: str, right: str) -> bool:

	if op == '=':
		return left == right
	if op == '!=':
		return left != right

	try:
		left, right = int(left, 0), int(right, 0)
	except ValueError:
		pass

	try:
		return {'<': left < right, '>': left > right, '<=': left <= right, '>=': left >= right}[op]
	except TypeError:
		return False
