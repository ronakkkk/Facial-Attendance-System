from validate_license import check_license
from multiprocessing import freeze_support
from parse_arguments import parse_argument

def run_fras(args):

    from FRAS import check_config, run_server, run_offline_recognition
    check_config(args)

    from src.load_config import CONFIG
    from collections import namedtuple

    nargs = namedtuple('nargs', ['t_fd', 'exp_r_fd', 't_id'])
    tup = nargs(0.8, 1.15, 0.2)

    # run_server(tup, CONFIG)
    if args.offline:
        run_offline_recognition(args, CONFIG)
    else:
        run_server(args, CONFIG)

# def create_db_cert(args):

#     from generate_db_cert import create_db_certificate, read_db_certificate
#     if args.write:
#         filename = args.filename
#         create_db_certificate(args.username, args.password, filename)

#     if args.read:
#         filename = args.filename
#         print(read_db_certificate(filename))

def run_bulk_upload(args):

    from FRAS import check_config
    check_config(args)

    from src.load_config import CONFIG
    # from FRAS import get_connection_string
    from src.bulk_upload import bulk_upload


    information_file_location = args.person_information_file_path
    picture_folder_location = args.picture_folder

    if information_file_location==None or picture_folder_location==None:
    	print("Usage --bulk_upload --person_information_file_path PERSON_INFORMATION_FILE_PATH --picture_folder PICTURE_FOLDER --log_folder LOG_FOLDER")
    	return

    log_folder = CONFIG['BULK_UPLOAD']['log_file_location']
    if args.log_folder is not None:
        log_folder = args.log_folder

    # face_connection_info, person_connection_info, _ = get_connection_string(None, CONFIG)

    #column_map = {b:a for a,b in CONFIG['BULK_UPLOAD_COLUMN_MAP'].items()}
    column_map = CONFIG['BULK_UPLOAD_COLUMN_MAP']
    #print(column_map)
    
    bulk_upload(information_file_location, picture_folder_location, log_folder, column_map)
    

if __name__ == '__main__':

    freeze_support()
    check_license()

    args = parse_argument()

    # if args.db_cert:
    #     create_db_cert(args)

    # if args.create_db:
    #     create_db_tables(args)

    print("Parameters of Recogserver in main: ", args.t_fd, args.t_id, args.exp_r_fd)

    if args.run_fras:
        run_fras(args)

    if args.bulk_upload:
        run_bulk_upload(args)