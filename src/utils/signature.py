import re
import os

def extract_boot_signature(path):

    if not os.path.exists(path):
        raise FileNotFoundError(f'Boot log not found at {path}')
    
    with open(path, 'r') as f:
        lines = f.readlines()

    pattern = r'Kernel panic[^\n]*\n.*?<([^>]+)>'
    signature_parts = []
    
    for line in lines:
        match = re.search(pattern, line, re.DOTALL)
        if match:
            signature_parts.append(match.group(1))
    
    return signature_parts