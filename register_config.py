from argparse import ArgumentParser
import configparser
import os

#
# @TODO: Add method to update partial settings
# @TODO: Add method to reset config settings
# @TODO: Add configuration for flask port
#

def build_argparser():

    parser = ArgumentParser()

    parser.add_argument('--camera_ipconfig', type=str, default='camera_ip_table.txt',
                        help="Name of the file containing information about IP Camera." \
                            "Format of the file: Every line should contain CAMERA_NAME,IP_ADDRESS_TO_CAMERA_FEED")
    parser.add_argument('--prototype_configfile', type=str, default='RecogServer/templates/config.ini',
                        help="Prototype config file")
    parser.add_argument('--reset', action='store_true',
                        help='Reset the configuration')
    parser.add_argument('--remove_all_ip_camera', action='store_true',
                        help='Remove/do not include ip cameras during reset/update/change.')
    
    return parser

class STATIC_CONFIG:

    def __init__(self):
        self.camera_config = {}

    def __read_file(self, config_file):

        with open(config_file, 'r') as fid:
            content = fid.read().split('\n')
        content = list(map(lambda x: x.strip('\r').split(','), content))
        return content

    def init(self, camera_config_file, config_file, remove_all_ip_camera=False):
        if os.path.exists(camera_config_file) and (not remove_all_ip_camera):
            i = 0
            for c in self.__read_file(camera_config_file):
                if len(c) > 1 and c[0][0] != '#':
                    i += 1
                    self.camera_config[f'IPCAMERA_{i}'] = {'camera_name' : c[0], 'camera_ip': c[1]}

        self.dump_settings(config_file)
    
    def dump_settings(self, config_file):
        print(f'Loading Config file {config_file}')
        config = configparser.ConfigParser(inline_comment_prefixes="#")
        config.read(config_file)

        old_camera_count = int(config['COMMON']['ip_camera_count'])

        update_dict = {'base_path':os.getcwd(), 'ip_camera_count':len(self.camera_config)}
        v = config['COMMON']
        keys = list(v.keys())
        for k in keys:
            if k not in update_dict:
                update_dict[k] = v[k]

        config.update({
                'COMMON': update_dict
                })
        
        if len(self.camera_config) > 0:
            config.update(self.camera_config)
        
        for i in range(len(self.camera_config), old_camera_count):
            config.remove_section(f'IPCAMERA_{i+1}')

        with open('config.ini', 'w') as fid:
            config.write(fid)

'''
if __name__ == '__main__':

    args = build_argparser().parse_args()
    config = STATIC_CONFIG()

    if (not os.path.exists('config.ini')) or args.reset: 
        config.init(args.camera_ipconfig, args.prototype_configfile, args.remove_all_ip_camera)
    else:
        config.init(args.camera_ipconfig, 'config.ini', args.remove_all_ip_camera)
'''