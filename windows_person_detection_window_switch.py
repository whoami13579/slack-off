import cv2
import supervision as sv
import numpy as np
from ultralytics import YOLO
import win32gui
import win32con
import win32process
import time
from typing import List, Tuple

def is_real_window(hwnd: int) -> bool:
    """Check if window is a real application window"""
    if not win32gui.IsWindowVisible(hwnd):
        return False
    if not win32gui.GetWindowText(hwnd):
        return False
    
    # Check if window has valid handle
    try:
        # Skip windows with certain styles (like hidden system windows)
        style: int = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        ex_style: int = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        
        # Filter out tool windows and other non-app windows
        if ex_style & win32con.WS_EX_TOOLWINDOW:
            return False
        if not (style & win32con.WS_VISIBLE):
            return False
            
        return True
    except:
        return False

def get_all_windows() -> List[Tuple[int, str]]:
    """Get all valid visible windows with titles"""
    windows: List[Tuple[int, str]] = []
    
    def enum_windows_callback(hwnd: int, results: List[Tuple[int, str]]) -> None:
        if is_real_window(hwnd):
            try:
                title: str = win32gui.GetWindowText(hwnd)
                if title:
                    results.append((hwnd, title))
            except:
                pass
    
    win32gui.EnumWindows(enum_windows_callback, windows)
    return windows

def display_windows(windows: List[Tuple[int, str]]) -> None:
    """Display numbered list of windows"""
    print("\n=== Open Application Windows ===")
    for i, (hwnd, title) in enumerate(windows[:10], 1):
        # Truncate long titles
        display_title: str = title[:70] + "..." if len(title) > 70 else title
        print(f"{i}. {display_title}")
    print("================================\n")


def convert_windows_list_to_list_of_strings(windows: List[Tuple[int, str]]) -> list[str]:
    result = []
    for i, (hwnd, title) in enumerate(windows[:10], 1):
        # Truncate long titles
        display_title: str = title[:70] + "..." if len(title) > 70 else title
        result.append(f"{i}. {display_title}")

    return result

def switch_to_window(hwnd: int, title: str) -> bool:
    """Bring the selected window to front"""
    # First verify the window still exists
    try:
        if not win32gui.IsWindow(hwnd):
            print("✗ Window no longer exists. Please refresh the list.")
            return False
    except:
        print("✗ Window handle is invalid. Please refresh the list.")
        return False
    
    try:
        # Method 1: Standard approach
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.1)
        
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(hwnd)
        
        print(f"✓ Switched to: {title}")
        return True
    
    except Exception as e:
        # Method 2: Using keyboard simulation workaround
        try:
            import win32api
            import win32com.client
            
            shell = win32com.client.Dispatch("WScript.Shell")
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            time.sleep(0.05)
            
            # Simulate Alt key press to allow SetForegroundWindow
            shell.SendKeys('%')
            time.sleep(0.05)
            win32gui.SetForegroundWindow(hwnd)
            
            print(f"✓ Switched to: {title}")
            return True
        except:
            pass
        
        # Method 3: Attach to thread
        try:
            # Get the thread id of the foreground window
            fg_thread: int = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[0]
            # Get the thread id of the target window
            target_thread: int = win32process.GetWindowThreadProcessId(hwnd)[0]
            
            if fg_thread != target_thread:
                # Attach to the foreground thread
                win32process.AttachThreadInput(fg_thread, target_thread, True)
                win32gui.SetForegroundWindow(hwnd)
                win32process.AttachThreadInput(fg_thread, target_thread, False)
            else:
                win32gui.SetForegroundWindow(hwnd)
            
            print(f"✓ Switched to: {title}")
            return True
        except:
            print(f"✗ Could not switch to this window. It may require administrator privileges.")
            print(f"   Try running this script as administrator.")
            return False

if __name__ == "__main__":
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


    windows: List[Tuple[int, str]] = get_all_windows()
    display_windows(windows[:10])
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
        if 0 < number:
            hwnd: int
            title: str
            hwnd, title = windows[0]
            if switch_to_window(hwnd, title):
                break

    cap.release()
    cv2.destroyAllWindows()
