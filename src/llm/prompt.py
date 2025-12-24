def get_prompt(delta_config):

    prompt = f"""
You're an expert in Linux kernel configuration development, debugging, and repair. Your task is to suggest which options
to enable or disable given a delta config between a working and non-bootable kernel configuration.

Delta Configuration:
{delta_config}

Please return ONLY a valid JSON object where each key is a CONFIG_OPTION and the value is 'y' or 'n':
{{
  'CONFIG_OPTION_1': 'y',
  'CONFIG_OPTION_2': 'n'
}}

Just return the JSON object without any additional text or explanation.
"""
    
    return prompt
