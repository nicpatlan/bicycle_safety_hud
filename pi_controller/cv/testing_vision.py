import cv2
from ultralytics import YOLO
video = cv2.VideoCapture(0)

model = YOLO('yolov8n.pt')
dict_classes = model.model.names

# car, motorcycle, bus, truck
# class_IDS = [2, 3, 5, 7]
class_IDS = [0]

VIDEO_SHAPE = video.read()[1].shape
IMG_AREA = VIDEO_SHAPE[0] * VIDEO_SHAPE[1]

def getImgArea():
    return IMG_AREA

cv2.imshow("frame", video.read()[1])

def get_obj_sizes():
    # Getting the current frame
    _, frame = video.read()

    y_hat = model.predict(frame, conf = 0.7, classes = class_IDS, device = 'cpu', verbose = False)
    
    # Getting the bounding boxes, confidence and classes of the recognize objects in the current frame.
    boxes   = y_hat[0].boxes.xyxy.cpu().numpy()
    conf    = y_hat[0].boxes.conf.cpu().numpy()
    classes = y_hat[0].boxes.cls.cpu().numpy()
    labels = [dict_classes[i] for i in classes]

    print(boxes)
    print(conf)
    print(labels)

    # Drawing bounding boxes
    for i in range(len(boxes)):
        x1, y1, x2, y2 = [int(f) for f in boxes[i]]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, labels[i], (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Displaying the frame
    cv2.imshow("frame", frame)

    return [int((x2 - x1) * (y2 - y1)) for x1, y1, x2, y2 in boxes]
