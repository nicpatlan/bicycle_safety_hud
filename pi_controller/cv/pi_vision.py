import cv2
import time

from pycoral.adapters import common
from pycoral.adapters import detect
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter

from picamera2 import Picamera2

picam2 = Picamera2()
# picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (640, 480)}))
picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (1280, 720)}))
picam2.start()

MODEL = "/home/maxmckelvey/BikePiController/efficientdet_lite2_448_ptq_edgetpu.tflite"
# MODEL = "/home/maxmckelvey/BikePiController/efficientdet_lite3_512_ptq_edgetpu.tflite"
LABELS = "/home/maxmckelvey/BikePiController/coco_labels.txt"

labels = read_label_file(LABELS)
interpreter = make_interpreter(MODEL)
interpreter.allocate_tensors()
print('tensors:', interpreter.get_input_details(), interpreter.get_output_details())

# COCO_IDS = [2, 3, 5, 7] # car, motorcycle, bus, truck
COCO_IDS = [0, 2, 3, 5, 7] # car, motorcycle, bus, truck
CONF = 0.6

def getSize(b: detect.BBox) -> int:
    try:
        return b.area()
    except:
        try:
            return b.area
        except:
            print("Error in getSize")
            return 0

test_frame = picam2.capture_array()
IMG_AREA = test_frame.shape[0] * test_frame.shape[1]

def getImgArea():
    return IMG_AREA

def get_obj_sizes():
    frame = picam2.capture_array()

    _, scale = common.set_resized_input(
        interpreter, frame.shape[:2][::-1], lambda size: cv2.resize(frame, size, interpolation=cv2.INTER_AREA)) # INTER_LINEAR for upsampling

    start = time.perf_counter()
    interpreter.invoke()
    inference_time = time.perf_counter() - start
    objs = detect.get_objects(interpreter, CONF, scale)
    print('%.2f ms' % (inference_time * 1000))

    print('-------RESULTS--------')
    if not objs:
        print('No objects detected')

    for obj in objs:
        print(labels.get(obj.id, obj.id))
        print('  id:    ', obj.id)
        print('  score: ', obj.score)
        print('  bbox:  ', obj.bbox)

    return [getSize(o.bbox) for o in objs if obj.id in COCO_IDS]
