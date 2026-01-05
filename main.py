import cv2
import supervision as sv
import numpy as np
from ultralytics import YOLO

model = YOLO('yolov8s.pt', verbose=False)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera")

width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
polygon = np.array([
    [0, 0],
    [width, 0],
    [width, height],
    [0, height]
])
zone = sv.PolygonZone(polygon=polygon)

# initiate annotators
box_annotator = sv.BoxAnnotator(thickness=4)
label_annotator = sv.LabelAnnotator(text_thickness=4, text_scale=2)
zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.WHITE, thickness=6, text_thickness=6, text_scale=4)


previous_number = 0
while True:
    ret, frame = cap.read()

    if not ret:
        print("Can't receive frame. Exiting ...")
        break

    if cv2.waitKey(30) == ord('q'):
        break

    # detect
    results = model.predict(source=frame, verbose=False)[0]
    detections = sv.Detections.from_ultralytics(results)
    detections = detections[detections.class_id == 0]
    zone.trigger(detections=detections)

    # annotate
    labels = [f"{model.names[class_id]} {confidence:0.2f}" for _, _, confidence, class_id, _, _ in detections]
    frame = box_annotator.annotate(scene=frame, detections=detections)
    frame = label_annotator.annotate(scene=frame, detections=detections, labels=labels)

    number = len(detections)
    if number != previous_number:
        print(number)
        previous_number = number
    cv2.imshow("frame", frame)

cap.release()
cv2.destroyAllWindows()
