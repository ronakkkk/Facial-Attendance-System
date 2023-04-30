import configparser

def set_value_in_property_file(file_path, section, key, value):
    config = configparser.RawConfigParser()
    config.read(file_path)
    config.set(section,key,value)                         
    cfgfile = open(file_path,'w')
    config.write(cfgfile, space_around_delimiters=False)  # use flag in case case you need to avoid white space.
    cfgfile.close()
    
    
if __name__=="__main__":
    from src.load_config import CONFIG
    set_value_in_property_file(CONFIG['CLEANUP']["config"], 'CLEANUP', "buffer",9)
    set_value_in_property_file(CONFIG['CLEANUP']["config"], 'CLEANUP', "buffer", int(CONFIG['CLEANUP']["buffer"])-1)