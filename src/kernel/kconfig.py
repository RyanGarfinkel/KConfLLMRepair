from src.utils import log
import os
import re

class KConfig:

    def __init__(self, path: str):

        self.path = path
        self.options = {}

        if not os.path.exists(path):
            log.error(f'KConfig file does not exist: {path}')
            raise FileNotFoundError(f'KConfig file does not exist: {path}')

        self.load()

    def load(self):
        
        yes_pattern = re.compile(r'^(CONFIG_[A-Za-z0-9_]+)=(.+)$')
        no_pattern = re.compile(r'^# (CONFIG_[A-Za-z0-9_]+) is not set$')


        with open(self.path, 'r') as f:
            for line in f:
                line = line.strip()
                
                if yes_pattern.match(line):
                    option, value = yes_pattern.match(line).groups()
                    self.options[option] = value

                elif no_pattern.match(line):
                    option = no_pattern.match(line).group(1)
                    self.options[option] = False
                
    def mv(self, dest):
        os.rename(self.path, dest)
        self.path = dest

    def cp(self, dest):
        with open(self.path, 'r') as src_file:
            with open(dest, 'w') as dest_file:
                dest_file.write(src_file.read())
