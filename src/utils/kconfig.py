from src.config import llm_config_dir
import re

misc_size_threshold = 500

def apply_llm_suggestions(commit_hash, config_path, options):

    print('Applying LLM suggestions to config...')

    with open(config_path, 'r') as f:
        lines = f.readlines()
    
    updated_lines = []
    for line in lines:

        stripped = line.strip()
        if stripped.startswith('CONFIG_'):
            option = stripped.split('=')[0].split()[0]

            if option in options:
                action = options[option]
                if action == 'y':
                    updated_lines.append(f'{option}=y\n')
                elif action == 'n':
                    updated_lines.append(f'# {option} is not set\n')
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    updated_config = f'{llm_config_dir}/{commit_hash}.config'
    
    with open(updated_config, 'w') as f:
        f.writelines(updated_lines)
    
    print(f'Applied {len(options)} suggestions.')

    return updated_config

def convert_config_to_dict(config_path):

    options = {}

    yes_pattern = re.compile(r'^(CONFIG_\w+)=(y|m|\d+)$')

    with open(config_path, 'r') as f:

        for line in f:
            line = line.strip()
            
            if not line:
                continue

            if match := yes_pattern.match(line):
                option, value = match.groups()
                options[option] = value
            
    return options

def calculate_delta(base_config, klocalizer_config):
    
    print('Calculating delta...')

    base_dict = convert_config_to_dict(base_config)
    klocalizer_dict = convert_config_to_dict(klocalizer_config)

    delta = {}

    for option in klocalizer_dict:
        if option not in base_dict or klocalizer_dict[option] != base_dict[option]:
            delta[option] = klocalizer_dict[option]
            base_dict.pop(option, None)

    for option in base_dict:
        delta[option] = 'n'

    edit_distance = sum(1 for _ in delta)

    print(f'Calculated delta with {edit_distance} changes.')

    return delta, edit_distance

def chunk_delta(delta):
    
    print('Chunking delts by subsystem...')

    subsystems = {}

    for option in delta:
        subsystem = option.split('_')[1]

        if subsystem not in subsystems:
            subsystems[subsystem] = {}

        subsystems[subsystem][option] = delta[option]

    print('Grouping smaller subsystems...')

    small_subsystems = {k: v for k, v in subsystems.items() if len(v) <= misc_size_threshold}
    for k in small_subsystems:
        subsystems.pop(k)

    misc_options = [{}]
    cur_len = 0

    while small_subsystems:
        subsystem, options = small_subsystems.popitem()
        sub_len = len(options)
        if cur_len + sub_len < misc_size_threshold:
            misc_options[-1].update(options)
            cur_len += sub_len
        else:
            misc_options.append(options)
            cur_len = sub_len
    
    for i, grouped in enumerate(misc_options):
        if grouped:
            subsystems[f'MISC_{i+1}'] = grouped

    print(f'Chunked delta into {len(subsystems)} subsystems.')
    print(f'There are {len(misc_options)} miscellaneous subsystems grouped.')
    print(f'Smallest subsystem size: {min(len(v) for v in subsystems.values())}')
    print(f'Largest subsystem size: {max(len(v) for v in subsystems.values())}')

    return subsystems
