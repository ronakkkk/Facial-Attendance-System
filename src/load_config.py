import configparser
from configparser import ExtendedInterpolation
import os

class LoadConfig():

    def __init__(self, config_file='config.ini'):
        self.CONFIG_FILE_NAME = os.path.join(os.getcwd(), config_file)

        if not os.path.exists(self.CONFIG_FILE_NAME):
            raise ValueError(f'Configuration File does not exists: {self.CONFIG_FILE_NAME}')

        self.cfg = configparser.ConfigParser(interpolation=ExtendedInterpolation(), inline_comment_prefixes="#")
        self.cfg.read(self.CONFIG_FILE_NAME)
    
    @property
    def config(self):
        return self.cfg
    
    

CONFIG = LoadConfig().config