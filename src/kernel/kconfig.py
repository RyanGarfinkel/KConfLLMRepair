from src.config import kernel_src
import os
import re

yes_pattern = re.compile(r'^(CONFIG_[A-Za-z0-9_]+)=(.+)$')
no_pattern = re.compile(r'^# (CONFIG_[A-Za-z0-9_]+) is not set$')

class KConfig:

    def __init__(self, path: str):

        if not os.path.exists(path):
            raise FileNotFoundError(f'Config file not found at {path}')
        
        self.path = path
        self._read_options()

    def _read_options(self):

        options = {}

        with open(self.path, 'r') as f:
            for line in f:
                line = line.strip()
                if yes_pattern.match(line):
                    option, value = yes_pattern.match(line).groups()
                    options[option] = value
                elif no_pattern.match(line):
                    option = no_pattern.match(line).group(1)
                    options[option] = False

        self.options = options

    def mv(self, dest):

        os.rename(self.path, dest)
        self.path = dest

    def cp(self, dest):

        with open(self.path, 'r') as src_file:
            with open(dest, 'w') as dest_file:
                dest_file.write(src_file.read())

        self.path = dest        

    def diff(self, config): # self - config

        delta_options = {}

        for option, value in self.options.items():

            if option not in config.options or config.options[option] != value:
                delta_options[option] = value

        return delta_options

    def refresh(self):

        self._read_options()