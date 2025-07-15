import pygetwindow as gw
import time
import sys
import cv2
import numpy as np
import mss
import win32api
import win32con
import signal
import random

# Templates
FIRST_BUTTON = "button.png"
SECOND_BUTTON = "again.png"
THRESHOLD = 0.8
MOVE_DURATION = 0.3
MOVE_STEPS = 20

running = True  # Global flag to stop loop

def signal_handler(sig, frame):
    global running
    print("\n[INFO] Ctrl+C detected. Exiting gracefully...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def bring_etheria_to_foreground():
    try:
        windows = gw.getWindowsWithTitle("Etheria:Restart")
        if not windows:
            print("Etheria:Restart window not found.")
            sys.exit(1)

        etheria_window = windows[0]

        if etheria_window.isMinimized:
            etheria_window.restore()

        etheria_window.activate()
        time.sleep(0.5)

        if etheria_window.left < 0 or etheria_window.top < 0:
            etheria_window.moveTo(0, 0)

        return etheria_window

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def get_screen_size():
    return win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)

def move_mouse_smoothly(x, y, duration=MOVE_DURATION, steps=MOVE_STEPS):
    current_x, current_y = win32api.GetCursorPos()
    dx = (x - current_x) / steps
    dy = (y - current_y) / steps
    delay = duration / steps

    for i in range(steps):
        win32api.SetCursorPos((int(current_x + dx * i), int(current_y + dy * i)))
        time.sleep(delay)

    win32api.SetCursorPos((x, y))  # Ensure final position

def native_click(x, y):
    screen_width, screen_height = get_screen_size()

    x = max(0, min(x, screen_width - 1))
    y = max(0, min(y, screen_height - 1))

    print(f"[INFO] Moving to click at: ({x}, {y})")

    try:
        move_mouse_smoothly(x, y)
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
    except Exception as e:
        print(f"[ERROR] Failed to click at ({x}, {y}): {e}")

def locate_and_click_button(window, template_path, label=""):
    with mss.mss() as sct:
        monitor = {
            "top": window.top,
            "left": window.left,
            "width": window.width,
            "height": window.height
        }

        screenshot = np.array(sct.grab(monitor))
        screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"[ERROR] Template image '{template_path}' not found.")
            sys.exit(1)

        result = cv2.matchTemplate(screenshot_rgb, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= THRESHOLD:
            click_x = max_loc[0] + window.left + template.shape[1] // 2
            click_y = max_loc[1] + window.top + template.shape[0] // 2

            native_click(click_x, click_y)
            print(f"[{time.strftime('%H:%M:%S')}] Clicked '{label}' at ({click_x}, {click_y})")
            return True
        else:
            print(f"[{time.strftime('%H:%M:%S')}] '{label}' not found (max_val={max_val:.2f})")
            return False

def main():
    window = bring_etheria_to_foreground()

    global running
    while running:
        clicked = locate_and_click_button(window, FIRST_BUTTON, "button.png")
        if clicked:
            delay = random.uniform(2, 5)
            print(f"[INFO] Waiting {delay:.2f} seconds before clicking 'again.png'...")
            time.sleep(delay)
            locate_and_click_button(window, SECOND_BUTTON, "again.png")
        time.sleep(1)

    print("[INFO] Script terminated.")


if __name__ == "__main__":
    main()
