from queue import Queue
import pyautogui, sys
import vision
import time, threading
from pynput import keyboard
from pynput.keyboard import Key, Controller, KeyCode


RESPAWN = "RESPAWN"
CHOOSE_GRENADE = "CHOOSE_GRENADE"
CLICK = "CLICK"
MOVE = "MOVE"
KEYCLICK = "KEYCLICK"
KEYPRESS = "KEYPRESS"
KEYRELEASE = "KEYRELEASE"

# this is (y, x)
CENTER = (468 + vision.SCREENGRABYOFFSET, 959)
KEYDELAY = 0.004


keyboard = Controller()
que = Queue()

def _pressRespawn():
    pyautogui.moveTo(800, 600)
    pyautogui.click()


def _chooseGrenade():
    pyautogui.moveTo(1013, 222)
    pyautogui.click()


def _click(delay):
    pyautogui.mouseDown(); time.sleep(delay); pyautogui.mouseUp()

def _moveto(pos):
    pyautogui.moveTo(pos[1], pos[0])

def _pressButton(key, delay, press=True, release=True):
    if press:
        keyboard.press(key)
        time.sleep(delay)
    if release:
        keyboard.release(key)
        time.sleep(delay)

def _eventDispatcher():
    print("Starting mouse event dispatcher")
    while True:
        event = que.get()
        action = event[0]

        if action == RESPAWN:
            _pressRespawn()
        elif action == CHOOSE_GRENADE:
            _chooseGrenade()
        elif action == CLICK:
            _click(KEYDELAY)
        elif action == MOVE:
            _moveto(event[1])
        elif action == KEYCLICK:
            _pressButton(event[1], KEYDELAY)
        elif action == KEYPRESS:
            _pressButton(event[1], KEYDELAY, press=True, release=False)
        elif action == KEYRELEASE:
            _pressButton(event[1], KEYDELAY, press=False, release=True)


def enqueue(event):
    if not isinstance(event, tuple):
        event = (event, )
    que.put(event)

thread = threading.Thread(target=_eventDispatcher)
thread.start()