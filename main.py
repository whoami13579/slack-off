import tkinter as tk
from tkinter import ttk
from typing import Optional
import cv2
from PIL import Image, ImageTk
from windows_person_detection_window_switch import get_all_windows, convert_windows_list_to_list_of_strings


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
        cameras = list_ports()
        cameras = cameras[1]
        cameras = [str(c) for c in cameras]
        
        app_windows = get_all_windows()
        app_windows = convert_windows_list_to_list_of_strings(app_windows)
        print(app_windows)

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

    def on_camera_change(self, _: tk.Event) -> None:
        index = int(self.camera_var.get())
        self.open_camera(index)

    def update_frame(self) -> None:
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
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
        print("Selected app window:", selected_window)


if __name__ == "__main__":
    root = tk.Tk()
    app = WebcamApp(root)
    root.mainloop()
