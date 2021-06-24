from pynput import keyboard
from pynput.keyboard import Key, Controller, KeyCode
import threading
import time
import subprocess


def forceQuitPython():
    subprocess.call(['C:\Windows\System32\cmd.exe', '/C', 'taskkill /F /IM PYTHON.EXE'])


class keylistener:
    def __init__(self):
        pass

    def start(self):
        thread = threading.Thread(target=self.listenEscape)
        thread.start()

    def on_press(self, key):
        # print('{0} pressed'.format(key))
        if key == Key.esc:
            forceQuitPython()
            return False

    def on_release(self, key):
        # print('{0} release'.format(key))
        if key == Key.esc:
            forceQuitPython()
            return False

    def listenEscape(self):   
        with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            print(".press escape to terminate script")
            listener.join()

listener = keylistener()
listener.start()
