from argparse import ArgumentParser

DEVICE_KINDS = ['CPU', 'GPU', 'FPGA', 'MYRIAD', 'HETERO', 'HDDL']

def build_parser():
    parser = ArgumentParser()


    parser.add_argument('--run_fras', action='store_true', help='Run FRAS.')
    parser.add_argument('--bulk_upload', action='store_true', help="Upload person information in bulk.")

    config = parser.add_argument_group('config.ini')
    config.add_argument('--camera_ipconfig', type=str, default='camera_ip_table.txt',
                        help="Name of the file containing information about IP Camera." \
                            "Format of the file: Every line should contain CAMERA_NAME,IP_ADDRESS_TO_CAMERA_FEED")
    config.add_argument('--prototype_configfile', type=str, default='RecogServer/templates/config.ini',
                        help="Prototype config file")
    config.add_argument('--reset', action='store_true',
                        help='Reset the configuration')
    config.add_argument('--update', action='store_true',
                        help='Update the camera configuration')
    config.add_argument('--remove_all_ip_camera', action='store_true',
                        help='Remove/do not include ip cameras during reset/update/change.')


    function = parser.add_argument_group('Function')
    function.add_argument('--capture', action='store_true', 
                          help="Run with this argument to fire up " \
                          "the flask app to enter new individuals in db")
    function.add_argument('--report', action='store_true',
                          help="Run with this argument to generate report.")
    # function.add_argument('--bulkupload', action='store_true',
    #                       help="Run with this argument to upload pics to the database.")
    function.add_argument('--offline', action='store_true',
                          help="Run recognition in offline mode")
    function.add_argument('--offline_type', type=str, choices=['bulk', 'single'], default='bulk',
                          help='Run offline recognition on bulk or not.')
    function.add_argument('--offline_file', type=str, default='offline.txt',
                          help="Run offline recognition on the video.")
    function.add_argument('--offline_rotation', type=int, choices=[90, 180, 270], default=None,
                          help="Rotate the loaded video by the specified angle")

    general = parser.add_argument_group('General')
    general.add_argument('--no_show', action='store_true',
                         help="(optional) Do not display output")
    general.add_argument('-tl', '--timelapse', action='store_true',
                         help="(optional) Auto-pause after each frame")
    general.add_argument('-cw', '--crop_width', default=0, type=int,
                         help="(optional) Crop the input stream to this width " \
                         "(default: no crop). Both -cw and -ch parameters " \
                         "should be specified to use crop.")
    general.add_argument('-ch', '--crop_height', default=0, type=int,
                         help="(optional) Crop the input stream to this height " \
                         "(default: no crop). Both -cw and -ch parameters " \
                         "should be specified to use crop.")
    
    gallery = parser.add_argument_group('Faces database')
    gallery.add_argument('--run_detector', action='store_true',
                         help="(optional) Use Face Detection model to find faces" \
                         " on the face images, otherwise use full images.")
    
    infer = parser.add_argument_group('Inference options')
    infer.add_argument('-v', '--verbose', action='store_true',
                       help="(optional) Be more verbose")
    infer.add_argument('-pc', '--perf_stats', action='store_true',
                       help="(optional) Output detailed per-layer performance stats")
    infer.add_argument('-t_fd', metavar='[0..1]', type=float, default=0.8,
                       help="(optional) Probability threshold for face detections" \
                       "(default: %(default)s)")
    infer.add_argument('-t_id', metavar='[0..1]', type=float, default=0.2,
                       help="(optional) Cosine distance threshold between two vectors " \
                       "for face identification (default: %(default)s)")
    infer.add_argument('-exp_r_fd', metavar='NUMBER', type=float, default=1.15,
                       help="(optional) Scaling ratio for bboxes passed to face recognition " \
                       "(default: %(default)s)")
    infer.add_argument('--allow_grow', action='store_true',
                       help="(optional) Allow to grow faces gallery and to dump on disk. " \
                       "Available only if --no_show option is off.")


    bulk_upload = parser.add_argument_group('bulk upload')
    bulk_upload.add_argument('--person_information_file_path', type=str, default=None, help="Location of the file containing person information.")
    bulk_upload.add_argument('--picture_folder', type=str, default=None, help="Location of picture folder.")
    bulk_upload.add_argument('--log_folder', type=str, default=None, help="Full path of log folder, if None value from config.ini will be used.")


    return parser

def parse_argument():
    args = build_parser().parse_args()
    return args
