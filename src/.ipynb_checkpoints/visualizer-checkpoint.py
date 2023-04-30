import cv2
import numpy as np
from collections import defaultdict
from .face_identifier import FaceIdentifier
from .global_vars import PEOPLE_TABLE
from .load_config import CONFIG
from .capture import VideoCaptureThreading

def open_input_stream(address):
    stream = address
    try:
        stream = int(address)
        cap = VideoCaptureThreading(stream)
        cap.start()
        # return cv2.VideoCapture(stream)#, cv2.CAP_DSHOW) # May need to remove cap_dshow for offline videos
    except ValueError:
        # return cv2.VideoCapture(stream)
        cap = cv2.VideoCapture(stream)

    return cap
    
def open_output_stream(address, fps, frame_size):
    output_stream = None
    if address != '':
        if not address.endswith('.avi'):
            pass #Write warning
    
        output_stream = cv2.VideoWriter(address, cv2.VideoWriter.fourcc(*'MJPG'), fps, frame_size)

    return output_stream


def get_best_screen_arrangement(n_screens):
    
    if n_screens == 1:
        return 1, 1
    
    if n_screens == 2:
        return 1, 2
    
    if n_screens == 3 or n_screens == 4:
        return 2, 2
    
    if n_screens == 5 or n_screens == 6:
        return 2, 3
    
    if n_screens >= 7 and n_screens <= 9:
        return 3, 3
    
    if n_screens >= 10 and n_screens <= 12:
        return 3, 4
    
    if n_screens >= 13 and n_screens <= 16:
        return 4, 4
    
    rows = int(np.floor(np.sqrt(n_screens)))
    cols = rows

    return rows, cols


class FrameProperties:

    def __init__(self):
        
        self.fps = 0
        self.video_fps = 0
        self.frame_size = (0, 0) #Width, Height
        self.frame_count = 0
        self.frame_num = 0
        self.frame_time = 0
        self.frame_start_time = 0
        self.detections = []
        self.labels = []
        self.output_stream = None

    def reset(self):

        self.fps = 0
        self.video_fps = 0
        self.frame_size = (0, 0) #Width, Height
        self.frame_count = 0
        self.frame_num = 0
        self.frame_time = 0
        self.frame_start_time = 0
        self.detections = []
        self.labels = []
        self.output_stream = None

    # Required Pickler handlers to dump object into shared memory
    def __getstate__(self):

        return (self.fps, self.video_fps, self.frame_size, self.frame_count,
                self.frame_num, self.frame_time, self.frame_start_time, self.detections,
                self.labels, self.output_stream)
    
    def __setstate__(self, state):

        (self.fps, self.video_fps, self.frame_size, 
        self.frame_count, self.frame_num, self.frame_time, 
        self.frame_start_time, self.detections,
        self.labels, self.output_stream) = state
    

class Visual:
    
    def __init__(self, source):
        self.source = source
        self.start_width = 0
        self.end_width = 0 #Not inclusive
        self.start_height = 0
        self.end_height = 0 #Not inclusive

    def update_frame_boundaries(self, height, width):
        self.start_width = width[0]
        self.end_width = width[1]
        self.start_height = height[0]
        self.end_height = height[1]
    
    def __repr__(self):
        return f'{self.source}-[{self.start_width}, {self.end_width}) x [{self.start_height}, {self.end_height})'
    
    @property
    def frame_boundaries(self):
        return ((self.start_width, self.end_width), (self.start_height, self.end_height))


class Visualizer:

    def __init__(self):

        self.logo_img = cv2.imread(CONFIG['RECOGNITION']['display_logo'])
        self.image_resized = False

    def resize_image(self, img, relative_shape, scale=0.2):

        if img.shape[0] > relative_shape[0] * scale or img.shape[1] > relative_shape[1] * scale:
            y = int(img.shape[0] * scale)
            x = int(img.shape[1] * scale)
            img = cv2.resize(img, dsize=(x, y))
            self.image_resized = True
        return img


    def add_logo(self, frame, alpha=0.4, beta=0.4, gamma=0):

        x_image, y_image, z_image = self.logo_img.shape
        overlay = cv2.addWeighted(frame[:x_image, :y_image, :z_image], alpha, self.logo_img, beta, gamma)
        frame[:x_image, :y_image, :z_image] = overlay
        return self.logo_img.shape


    def draw_text_with_background(self, frame, text, origin, font=cv2.FONT_HERSHEY_SIMPLEX,
                                    scale=1.0, color=(0, 0, 0), thickness=1, bgcolor=(255, 255, 255)):

        text_size, baseline = cv2.getTextSize(text, font, scale, thickness)
        cv2.rectangle(frame,
                      tuple((origin + (0, baseline)).astype(int)),
                      tuple((origin + (text_size[0], -text_size[1])).astype(int)),
                      bgcolor, cv2.FILLED)
        cv2.putText(frame, text,
                    tuple(origin.astype(int)),
                    font, scale, color, thickness)
        return text_size, baseline


    def draw_detection_roi(self, frame, roi, identity, label, people_list):
        
        # Draw identity label
        text_scale = 0.5
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize("H1", font, text_scale, 1)
        line_height = np.array([0, text_size[0][1]])

        people = people_list.find_identity(label)

        text = people[PEOPLE_TABLE.name.value]
        threat = people[PEOPLE_TABLE.threat.value]

        if identity.id != FaceIdentifier.UNKNOWN_ID:
            text += ''

        rectangle_color = tuple([0, 165, 255])
        bg_color = tuple([255, 255, 255])
        text_color = tuple([0, 0, 0])

        if threat == "y":
            rectangle_color = tuple([0, 0, 255])
            bg_color = tuple([0, 0, 255])
            text_color = tuple([255, 255, 255])
        elif threat == "n":
            rectangle_color = tuple([0, 255, 0])

        self.draw_text_with_background(frame, text,
                                       roi.position - line_height * 0.5,
                                       font, scale=text_scale,
                                       color=text_color, bgcolor=bg_color)

        cv2.rectangle(frame,
                      tuple(roi.position), tuple(roi.position + roi.size),
                      rectangle_color, 2)


    def draw_detection(self, frame, detections, labels, people_list):
        
        for vals in zip(*detections, labels):
            roi, _, identity, label = vals
            self.draw_detection_roi(frame, roi, identity, label, people_list)


    def draw_status(self, frame, detections, fps, frame_time,camera_name=None):

        end_positions = self.add_logo(frame)
        origin = np.array([end_positions[1]+10, 11])
        color = (10, 160, 10)
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_scale = 0.5
        text_scale2=0.5
        text_size1=None
        if camera_name:
            text_size1, _ = self.draw_text_with_background(frame,camera_name,origin, font, text_scale2, color)
        else:
            text_size1=(0,0)
        text_size2, _ = self.draw_text_with_background(frame,
                                                      "Frame time: %.3fs" % (frame_time),
                                                      (origin + (0, text_size1[1] * 1.5)), font, text_scale, color)
        self.draw_text_with_background(frame,
                                       "FPS: %.1f" % (fps),
                                       (origin + (0,text_size1[1] * 1.5+text_size2[1] * 1.5)), font, text_scale, color)


    def visualize(self, display_memory, control_panel, people_list, monitor_memory):
        
        camera_name = None
        while (not control_panel.should_stop()) and (not control_panel.is_close_all()):
            
            prop = display_memory.get_frame()
            if prop:
                camera_id, frame, frame_properties = prop

                if not self.image_resized:
                    self.logo_img = self.resize_image(self.logo_img, frame.shape)

                camera_name = control_panel.get_camera_name(camera_id)

                self.draw_detection(frame, frame_properties.detections, 
                                        frame_properties.labels, people_list)
                self.draw_status(frame, frame_properties.detections, 
                                    frame_properties.fps, frame_properties.frame_time,camera_name)
                
                if control_panel.should_display(camera_id):
                    cv2.namedWindow(camera_name, cv2.WND_PROP_FULLSCREEN)
                    cv2.setWindowProperty(camera_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                    cv2.imshow(camera_name, frame)
                    cv2.waitKey(1)
                else:
                    cv2.waitKey(1)
                    cv2.destroyWindow(camera_name)

                if control_panel.should_display_monitor():
                    monitor_memory.add_frame(camera_id, frame, frame_properties)

        if camera_name:
            cv2.waitKey(1)
            cv2.destroyWindow(camera_name)
    
    def writer(self, display_memory, people_list, progress_memory=None):
        
        writer_container = defaultdict(lambda: None)

        while 1:

            prop = display_memory.get_frame()
            if prop:
                _, frame, frame_properties = prop
                if len(frame) > 0:

                    if frame_properties.output_stream not in writer_container:
                        writer_container[frame_properties.output_stream] = open_output_stream(
                            frame_properties.output_stream,
                            frame_properties.video_fps,
                            frame_properties.frame_size
                        )
                    writing_object = writer_container[frame_properties.output_stream]

                    if not self.image_resized:
                        self.logo_img = self.resize_image(self.logo_img, frame.shape)

                    self.draw_detection(frame, frame_properties.detections, 
                                            frame_properties.labels, people_list)
                    self.draw_status(frame, frame_properties.detections, 
                                        frame_properties.fps, frame_properties.frame_time)

                    writing_object.write(frame)

                else:
                    break
        
        for keys in writer_container.keys():
            writer_container[keys].release()