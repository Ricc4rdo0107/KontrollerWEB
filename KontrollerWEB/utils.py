import cv2
import base64
import pyautogui as pg
from random import randint

from pymsgbox import confirm as msgbox_alert
from threading import Thread
import ctypes

import mss
import mss.tools


def start_new_thread(function, args=None):
    if args is None:
        Thread(target=function).start()
    else:
        Thread(target=function, args=args).start()


def tmpname():
    return f"tmp{randint(9999,999999999)}.png"


def to_base64(string:str) -> str:
    return base64.b64encode(string.encode("ascii")).decode()


def screenshot_bytes():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        im = sct.grab(monitor)
        raw_bytes = mss.tools.to_png(im.rgb, im.size)
        return raw_bytes
    
def gen_screenshots():
    while True:
        yield (b"--frame\r\n"
               b'Content-Type: image/jpeg\r\n\r\n' + screenshot_bytes() + b'\r\n')



def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)
    #Mbox('Your title', 'Your text', 1)

def gen_frames(camera=None):
    if camera is None:
        camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()  # read the camera frame
        frame = cv2.flip(frame, 1)
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    camera.release()


def save_selphie(filename, camera=None):
    if camera is None:
        camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    cv2.imwrite(filename, frame)
    camera.release()

def save_screenshot(filename):
    screenshot = pg.screenshot(filename)