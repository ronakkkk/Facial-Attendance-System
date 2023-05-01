from parse_arguments import parse_argument
from src.shared_memory import SharedMemory
from multiprocessing import Process, freeze_support
from werkzeug.serving import make_server
import threading
import os
import time
from datetime import date, timedelta
from flask import Flask
app = Flask(__name__)

class WorkerThread(threading.Thread):

    def __init__(self, control_panel, vector, people_list, face_db_file_path, person_db_file_path,config):
        threading.Thread.__init__(self)
        self.control_panel = control_panel
        self.vector = vector
        self.people_list = people_list
        self.face_db_file_path = face_db_file_path
        self.person_db_file_path = person_db_file_path
        self.config=config

    def run(self):
        worker(self.control_panel, self.vector, self.people_list, self.face_db_file_path, self.person_db_file_path,self.config)

class WebappProcess(threading.Thread):
#class WebappProcess(Process):

    def __init__(self, app, host='127.0.0.1', port=5000, ssl_context=None):
        threading.Thread.__init__(self)
        #Process.__init__(self)
        self.server = make_server(host=host,
                                  port=port,
                                  app=app,
                                  ssl_context=ssl_context,
                                  threaded=True)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        
        
import configparser

def set_value_in_property_file(file_path, section, key, value):
    config = configparser.RawConfigParser()
    config.read(file_path)
    config.set(section,key,value)                         
    cfgfile = open(file_path,'w')
    config.write(cfgfile, space_around_delimiters=False)  # use flag in case case you need to avoid white space.
    cfgfile.close()
        

def worker(control_panel, vector, people_list, face_db_file_path, person_db_file_path,CONFIG):

    # from src.report import create_report
#     import glob
    
    print('Starting Worker')
    
#     print("buffer: ",int(CONFIG['CLEANUP']["buffer"]))
    if int(CONFIG['CLEANUP']["buffer"])<=0:
        temp_path=os.path.join(CONFIG['TEMP']['temp_processing_path'])
        fnames = os.listdir(temp_path)
        for f in fnames:
            try:
                os.unlink(os.path.join(temp_path,f))
            except Exception as e:
                print("Error in removing file: ",e)
                pass
        set_value_in_property_file(CONFIG['CLEANUP']["config"], 'CLEANUP', "buffer",7)

                

    prev_date = date.today()
    while (not control_panel.should_stop()) and (not control_panel.is_close_all()):
        if control_panel.get_update_cache():
            vector.set_up_db(db_file=face_db_file_path)
            people_list.load_people_list(db_file=person_db_file_path)
            control_panel.reset_update_cache()

        if (date.today() - prev_date).days > 0:
            set_value_in_property_file(CONFIG['CLEANUP']["config"], 'CLEANUP', "buffer", int(CONFIG['CLEANUP']["buffer"])-1)
            
            # create_report(store=True)
            prev_date = date.today()
            if not update_expiration():
                control_panel.set_expiration()
                print(f'License Expired yesterday {prev_date - timedelta(1)}')
                break

    print('Terminated worker')

def check_config(args):

    from register_config import STATIC_CONFIG
    conf = STATIC_CONFIG()
    if (not os.path.exists('config.ini')) or args.reset:
        conf.init(args.camera_ipconfig, args.prototype_configfile, args.remove_all_ip_camera)
    elif args.update:
        conf.init(args.camera_ipconfig, 'config.ini', args.remove_all_ip_camera)


def run_query_processor(dbs, control_panel, db_memory):

    print('Starting Query Processor')

    from src.query_processor import QueryProcessor
    query_processor = QueryProcessor(dbs)
    query_processor.process_queries(control_panel, db_memory)

    print('Terminated query processor')



def run_webapp(camera_ids, control_panel, webdisplay, progress_bar_memory, CONFIG):

    print('Starting Webapp')

    from src.webapp_utils import memory_container
    memory_container.add_memory('control_panel', control_panel)
    memory_container.add_memory('webdisplay', webdisplay)
    memory_container.add_memory('camera_ids', camera_ids)
    memory_container.add_memory('progress_bar', progress_bar_memory)

    from src.webapp import app
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['UPLOAD_FOLDER'] = CONFIG['UPLOAD']['webapp_upload_path']
    app.config['TEMP_FOLDER'] = CONFIG['TEMP']['temp_processing_path']
    app.config['SECRET_KEY'] = 'fras' # Required better secret key

    #app.run(port=int(CONFIG['GUI']['port']), host='0.0.0.0', ssl_context=('server.crt', 'server.key'))

    # Need to understand how to handle multiple requests before using belowcode.

    server = WebappProcess(app, port=int(CONFIG['GUI']['port']), ssl_context=('server.crt', 'server.key'))
    server.start()

    while control_panel.should_run_webapp() and (not control_panel.should_stop()):

        if not server.is_alive():
            server = WebappProcess(app, port=int(CONFIG['GUI']['port']), ssl_context=('server.crt', 'server.key'))
            server.start()

    control_panel.stop_webapp()
    control_panel.set_close_all()
    server.shutdown()
    server.join()

    print('Terminated webapp')

def run_server(args, CONFIG):

    # https://stackoverflow.com/questions/21120947/catching-keyboardinterrupt-in-python-during-program-shutdown
    face_db_file_path = os.path.normpath(CONFIG['DB']['face_db'])
    person_db_file_path = os.path.normpath(CONFIG['DB']['person_db'])

    dbs = [('face', face_db_file_path), ('person', person_db_file_path)]

    shared_memory_manager = SharedMemory()
    shared_memory_manager.start()
    vectors = shared_memory_manager.Vectors()
    people_list = shared_memory_manager.Identities()
    control_panel = shared_memory_manager.ControlPanel()
    webdisplay = shared_memory_manager.Display()
    db_memory = shared_memory_manager.Database()
    progress_bar_memory = shared_memory_manager.ProgressBar()

    print('run_server in fras.py', face_db_file_path)
    # vectors.set_up_db(db_file=face_db_file_path)
    people_list.load_people_list(db_file=person_db_file_path)

    process_container = {} # Will store processes
    thread_container = {}  # Will store worker thread

    camera_ids = {}

    query_proc = lambda: Process(name='query_processor',
                                 target=run_query_processor,
                                 args=(dbs, control_panel, db_memory))
    #process_container.append([None, query_proc])
    process_container['query'] = [None, query_proc]

    control_panel.start_webapp()
    webapp_proc = Process(name='webapp',
        target=run_webapp,
        args=(list(camera_ids.keys()), control_panel, webdisplay, progress_bar_memory, CONFIG))

    # First start
    freeze_support()
    webapp_proc.start()

    work_th = lambda: WorkerThread(control_panel, vectors, people_list, face_db_file_path, person_db_file_path,CONFIG)
    #thread_container.append([None, work_th])
    thread_container['woker'] = [None, work_th]


    webapp_proc.join()
    shared_memory_manager.shutdown()
    shared_memory_manager.join()

    print('Terminated memory')
    print('Exiting')


if __name__ == '__main__':
    # freeze_support()
    args = parse_argument()
    check_config(args)
    from src.load_config import CONFIG
    app = run_server(args, CONFIG)