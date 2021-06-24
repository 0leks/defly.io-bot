
from pynput import keyboard
from pynput.keyboard import Key, Controller, KeyCode
import time


time.sleep(2)

keyboard = Controller()
keyboard.press(Key.space)

