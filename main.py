import tkinter as tk
from tkinter import ttk
from typing import Optional
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
import supervision as sv
import numpy as np
from windows_person_detection_window_switch import get_all_windows, convert_windows_list_to_list_of_strings, switch_to_window


def list_ports():
    """
    Test the ports and returns a tuple with the available ports 
    and the ones that are working.
    """
    is_working = True
    dev_port = 0
    working_ports = []
    available_ports = []
    while is_working:
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            is_working = False
            print("Port %s is not working." %dev_port)
        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                print("Port %s is working and reads images (%s x %s)" %(dev_port,h,w))
                working_ports.append(dev_port)
            else:
                print("Port %s for camera ( %s x %s) is present but does not reads." %(dev_port,h,w))
                available_ports.append(dev_port)
        dev_port +=1
    return available_ports,working_ports

class WebcamApp:
    def __init__(self, window: tk.Tk) -> None:
        self.window = window
        self.window.title("Webcam Viewer")


        # ---------- Detect Webcams ----------
        cameras = list_ports()
        cameras = cameras[1]
        cameras = [str(c) for c in cameras]
        
        # ---------- Detect App Windows ----------
        self.windows = get_all_windows()
        app_windows = get_all_windows()
        app_windows = convert_windows_list_to_list_of_strings(app_windows)
        self.target_window_number = 0

        # ---------- Dropdown ----------
        self.camera_var = tk.StringVar(value="0")

        self.camera_selector = ttk.Combobox(
            window,
            textvariable=self.camera_var,
            values=cameras,
            state="readonly",
            width=10,
        )
        self.camera_selector.pack(pady=5)
        self.camera_selector.bind("<<ComboboxSelected>>", self.on_camera_change)


        # ---------- App Window Dropdown ----------
        self.app_window_var = tk.StringVar(
            value=app_windows[0] if app_windows else ""
        )

        self.app_window_selector = ttk.Combobox(
            window,
            textvariable=self.app_window_var,
            values=app_windows,
            state="readonly",
            width=40,
        )
        self.app_window_selector.pack(pady=5)
        self.app_window_selector.bind(
            "<<ComboboxSelected>>", self.on_app_window_change
        )

        # ---------- Setup Human Detection ----------
        self.model = YOLO('yolov8s.pt', verbose=False)
        width = 0
        height = 0
        self.polygon = np.array([
            [0, 0],
            [width, 0],
            [width, height],
            [0, height]
        ])
        self.zone = sv.PolygonZone(polygon=self.polygon)

        # initiate annotators
        self.box_annotator = sv.BoxAnnotator(thickness=4)
        self.label_annotator = sv.LabelAnnotator(text_thickness=4, text_scale=2)
        self.zone_annotator = sv.PolygonZoneAnnotator(zone=self.zone, color=sv.Color.WHITE, thickness=6, text_thickness=6, text_scale=4)

        # ---------- Video ----------
        self.label = tk.Label(window)
        self.label.pack()

        self.cap: Optional[cv2.VideoCapture] = None
        self._imgtk: Optional[ImageTk.PhotoImage] = None

        self.open_camera(0)
        self.update_frame()

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)


    def open_camera(self, index: int) -> None:
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()

        self.cap = cv2.VideoCapture(index)

        width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.polygon = np.array([
            [0, 0],
            [width, 0],
            [width, height],
            [0, height]
        ])
        self.zone = sv.PolygonZone(polygon=self.polygon)

        # initiate annotators
        self.box_annotator = sv.BoxAnnotator(thickness=4)
        self.label_annotator = sv.LabelAnnotator(text_thickness=4, text_scale=2)
        self.zone_annotator = sv.PolygonZoneAnnotator(zone=self.zone, color=sv.Color.WHITE, thickness=6, text_thickness=6, text_scale=4)

    def on_camera_change(self, _: tk.Event) -> None:
        index = int(self.camera_var.get())
        self.open_camera(index)

    def update_frame(self) -> None:
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                results = self.model.predict(source=frame, verbose=False)[0]
                detections = sv.Detections.from_ultralytics(results)
                detections = detections[detections.class_id == 0]
                self.zone.trigger(detections=detections)

                # annotate
                labels = [f"{self.model.names[class_id]} {confidence:0.2f}" for _, _, confidence, class_id, _, _ in detections]
                frame = self.box_annotator.annotate(scene=frame, detections=detections)
                frame = self.label_annotator.annotate(scene=frame, detections=detections, labels=labels)

                number = len(detections)
                if 0 < number:
                    hwnd, title = self.windows[self.target_window_number]
                    switch_to_window(hwnd, title)

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                img = Image.fromarray(frame)
                self._imgtk = ImageTk.PhotoImage(img)
                self.label.configure(image=self._imgtk)

        self.window.after(10, self.update_frame)

    def on_close(self) -> None:
        if self.cap is not None:
            self.cap.release()
        self.window.destroy()
    
    def on_app_window_change(self, _: tk.Event) -> None:
        selected_window = self.app_window_var.get()
        self.target_window_number = int(selected_window.split(".")[0]) - 1
        print(self.target_window_number)
        print("Selected app window:", selected_window)


if __name__ == "__main__":
    root = tk.Tk()
    app = WebcamApp(root)
    root.mainloop()
