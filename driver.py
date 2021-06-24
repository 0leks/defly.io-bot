import numpy as np
from queue import Queue
from queue import SimpleQueue
import queue
import threading, time
import ctypes
from pynput import keyboard
from pynput.keyboard import Key, Controller, KeyCode
from random import randrange
import math
import cv2


import escapelistener
import mousecontroller as mc
import vision
from gui import GUI


SAVE_IMAGES = True
START_BUTTON_DELAY = 2

EXIT_EVENT = "EXIT"
eventQ = Queue()
actionQ = Queue()

highPriorityQ = SimpleQueue()
lowPriorityQ = SimpleQueue()
graphicalQ = SimpleQueue()
currentDirectionQ = SimpleQueue()
saveImageQ = SimpleQueue()
currentDirectionQForImage = SimpleQueue()



directions = [
    (-1,0),
    (-1,1),
    (0,1),
    (1,1),
    (1,0),
    (1,-1),
    (0,-1),
    (-1,-1),
]
NUM_DIRS = len(directions)
ORTH_ADD = int(NUM_DIRS/4)
orthogonal = [(d[0], d[1]) for d in (directions[ORTH_ADD:] + directions[:ORTH_ADD])]
directionToOrthogonal = {dire: orth for dire, orth in zip(directions, orthogonal)}
print(directionToOrthogonal)



def keyClick(keyboard, key, delay):
    keyboard.press(key)
    if delay > 0:
        time.sleep(delay)
    keyboard.release(key)

def getThreadID(thread):
    if hasattr(thread, '_thread_id'):
        return thread._thread_id
    for id, t in threading._active.items():
        if t is thread:
            return id

def raiseThreadException(thread):
    thread_id = getThreadID(thread)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        print('Exception raise failure')



def checkReachedEdge(position, direction):
    if direction[0] == -1:
        if position[0] == 0:
            return True
    if direction[0] == 1:
        if position[0] == vision.MAXY:
            return True
    if direction[1] == -1:
        if position[1] == 0:
            return True
    if direction[1] == 1:
        if position[1] == vision.MAXX:
            return True
    return False


def handleDirection(direction, keyboard, pressorrelease):
    func = keyboard.press if pressorrelease else keyboard.release

    if direction[0] == 1:
        func(Key.down)
    elif direction[0] == -1:
        func(Key.up)

    if direction[1] == 1:
        func(Key.right)
    elif direction[1] == -1:
        func(Key.left)


def chooseExtraTime(secondsSinceLastEncounter):
    return 1 + randrange(6) + int(secondsSinceLastEncounter/20)

def switchDirections(keyboard, old, new, extratime):
    if old is not None:
        handleDirection(old, keyboard, False)
    if new is not None:
        handleDirection(new, keyboard, True)
    return new, time.time() + extratime


def getMousePositionInDirection(direction, distance, orthogonal, offset):
    return (mc.CENTER[0] + direction[0] * distance + orthogonal[0] * offset,
            mc.CENTER[1] + direction[1] * distance + orthogonal[1] * offset)

def actionLoop():
    time.sleep(START_BUTTON_DELAY)
    END = False
    directions = [
        (-1,0),
        (-1,1),
        (0,1),
        (1,1),
        (1,0),
        (1,-1),
        (0,-1),
        (-1,-1),
    ]
    NUM_DIRS = len(directions)
    ORTH_ADD = int(NUM_DIRS/4)
    orthogonal = [(d[0], d[1]) for d in (directions[ORTH_ADD:] + directions[:ORTH_ADD])]
    print(orthogonal)
    currentIndex = 0
    currentDirection = directions[currentIndex]
    keyboard = Controller()
    keyboard.press(Key.space)
    currentDirection, lastDirectionTime = switchDirections(keyboard, None, currentDirection, chooseExtraTime(0))
    lastEncounter = time.time()
    nextTimeTargetNotTerritory = time.time()
    nextRandomBump = 0
    SCAN_RANGE = 60
    try:
        while not END:
            data = highPriorityQ.get()
            highlighted = data['hsvimage']
            position = data['playerPos']

            if not data['enemyNearby'] and data['percentenemyterritory'] == 0 and time.time() > nextTimeTargetNotTerritory:
                    mc.enqueue((mc.MOVE, mc.CENTER))
                    nextTimeTargetNotTerritory = time.time() + 2 + randrange(13)
                    if data['percentmyterritory'] >= 0.45:
                        targetLocation = data['closestNotTerritory']
                        delta = [targetLocation[0] - position[0], targetLocation[1] - position[1]]
                        magnitude = math.sqrt(delta[0]*delta[0] + delta[1]*delta[1])
                        if magnitude > 0:
                            delta = [delta[0] / magnitude, delta[1] / magnitude]
                            delta[0] = 1 if delta[0] > 0.5 else (-1 if delta[0] < -0.5 else 0)
                            delta[1] = 1 if delta[1] > 0.5 else (-1 if delta[1] < -0.5 else 0)
                            newDirection = tuple(delta)
                            currentIndex = directions.index(newDirection)
                            currentDirection, lastDirectionTime = switchDirections(keyboard, currentDirection, newDirection, chooseExtraTime(time.time() - lastEncounter))
                            print(f"moving towards the nearest not territory: {targetLocation}, new direction: {newDirection}")

            if time.time() > lastDirectionTime:
                newIndex = (currentIndex + NUM_DIRS - 1) % NUM_DIRS
                newDirection = directions[newIndex]
                isClear, _ = vision.isDirectionClear(highlighted, newDirection, SCAN_RANGE+10, orthogonal[newIndex])
                if isClear == 999:
                    print(f"CCW curpos: {position},  {currentDirection} -> {newDirection}")
                    currentDirection, lastDirectionTime = switchDirections(keyboard, currentDirection, newDirection, chooseExtraTime(time.time() - lastEncounter))
                    currentIndex = newIndex

            distances = {}
            offsets = {}
            SCAN_RANGE = 60 if data['enemyNearby'] else 35
            isClear, offset = vision.isDirectionClear(highlighted, currentDirection, SCAN_RANGE, orthogonal[currentIndex])
            distances[currentIndex] = isClear
            offsets[currentIndex] = offset
            if isClear != 999:
                lastEncounter = time.time()

            reachedEdge = checkReachedEdge(position, currentDirection)
                
            if isClear != 999 or reachedEdge:
                # handleDirection(currentDirection, keyboard, False)
                attempts = 0
                newIndex = currentIndex
                newDirection = currentDirection
                while (attempts < NUM_DIRS) and (isClear != 999 or reachedEdge):
                    reachedEdge = False
                    attempts = attempts + 1
                    newIndex = (newIndex + 1) % NUM_DIRS
                    newDirection = directions[newIndex]
                    isClear, offset = vision.isDirectionClear(highlighted, newDirection, SCAN_RANGE, orthogonal[newIndex])
                    distances[newIndex] = isClear
                    offsets[newIndex] = offset
                    if isClear != 999:
                        lastEncounter = time.time()
                    reachedEdge = checkReachedEdge(position, newDirection)

                print(f"pos: {position}, {attempts} switch to going {newDirection}")
                if attempts == NUM_DIRS:
                    bestIndex = max(distances, key=distances.get)
                    newDirection = directions[bestIndex]
                    print(f"Choosing best dir {bestIndex} out of {distances}")
                currentDirection, lastDirectionTime = switchDirections(keyboard, currentDirection, newDirection, chooseExtraTime(time.time() - lastEncounter))
                currentIndex = newIndex

            currentDirectionQ.put(currentDirection)
            if SAVE_IMAGES:
                currentDirectionQForImage.put(currentDirection)

    finally:
        print("exiting actionLoop")
    currentDirection, lastDirectionTime = switchDirections(keyboard, currentDirection, None, 0)
    keyboard.release(Key.space)


def getEnemyLocAdjusted(enemyterritory, currentDirection):
    enemyLoc = vision.getClosestEnemyLoc(enemyterritory)
    if enemyLoc is not None:
        enemyLocAdjusted = enemyLoc
        if currentDirection is not None: 
            enemyLocAdjusted = (enemyLoc[0] - currentDirection[0]*20, enemyLoc[1] - currentDirection[1]*20)
            enemyLocAdjusted = (min(max(enemyLocAdjusted[0], vision.SCREENGRABYOFFSET), 1080 - 41), min(max(enemyLocAdjusted[1], 0), 1919))
    return enemyLoc


def getMostRecent(Q):
    thing = None
    if not Q.empty():
        thing = Q.get()
        while not Q.empty():
            thing = Q.get()
    return thing


UPGRADE_PRIORITY = [6, 5, 0, 4]
def lowPriorityLoop():
    time.sleep(START_BUTTON_DELAY)
    print(f"starting lowPriorityLoop")
    print(f"Pressing spacebar")
    mc.enqueue((mc.KEYPRESS, Key.space))
    nextTimeToUseSuperpower = time.time()

    while True:
        data = lowPriorityQ.get()

        if data is None:
            print(f"lowPriorityLoop exiting")
            break

        if "respawnmenu" in data:
            print(f"lowPriorityLoop respawning")
            mc.enqueue(mc.RESPAWN)
            time.sleep(1)
            continue
        
        if "upgrades" in data:
            upgrades = data["upgrades"]
            for upgradeIndex in UPGRADE_PRIORITY:
                if upgrades[vision.UPGRADE_NAMES[upgradeIndex]] < 8:
                    mc.enqueue((mc.KEYCLICK, KeyCode.from_char(f"{upgradeIndex+1}")))
                    print(f"lowPriorityLoop upgrading {vision.UPGRADE_NAMES[upgradeIndex]} to {upgrades[vision.UPGRADE_NAMES[upgradeIndex]] + 1}")
                    time.sleep(0.1)
                    break

        if "selectsuperpower" in data:
            print(f"lowPriorityLoop choosing grenade")
            mc.enqueue(mc.CHOOSE_GRENADE)
            time.sleep(0.2)
            continue
        
        currentDirection = getMostRecent(currentDirectionQ)
        enemyLoc = getEnemyLocAdjusted(data["enemyterritory"], currentDirection)
        if enemyLoc is not None:
            enemyLoc = (enemyLoc[0]*vision.SHRINKFACTOR + vision.SCREENGRABYOFFSET, enemyLoc[1]*vision.SHRINKFACTOR)
            mc.enqueue((mc.MOVE, enemyLoc))
            if time.time() > nextTimeToUseSuperpower:
                print(f"lowPriorityLoop throwing grenade at {enemyLoc}")
                mc.enqueue((mc.KEYCLICK, KeyCode.from_char('e')))
                nextTimeToUseSuperpower = time.time() + 5.05 # actual cd is 30s but its okay to try to spam a bit
                if not data['enemyNearby']:
                    print(f"lowPriorityLoop shooting at {enemyLoc}")
                    mc.enqueue((mc.CLICK))


def applyScaleFactor(pos, factor):
    newpos = (pos[0]*factor, pos[1]*factor)
    newpos = (newpos[0] + (1 if newpos[0]%2 == 1 else 0), newpos[1] + (1 if newpos[1]%2 == 1 else 0))
    return newpos 


def drawX(image, location, size, color):
    if not hasattr(drawX, 'xarrays'):
        drawX.xarrays = {}

    if size not in drawX.xarrays:
        xarray = np.ones((size, size), dtype=bool)
        xarray[0, 0] = False
        xarray[0, -1] = False
        xarray[-1, 0] = False
        xarray[-1, -1] = False
        # xarray = np.zeros((size, size), dtype=bool)
        # for i in range(size):
        #     xarray[i, i] = True
        #     xarray[size-i-1, i] = True
        drawX.xarrays[size] = xarray
    snippet = image[location[0]:location[0]+size, location[1]:location[1]+size]
    snippet[drawX.xarrays[size]] = color


def applyImageWithBorder(canvas, image, x, y, borderwidth, bordercolor=(255, 255, 255)):
    if borderwidth > 0:
        canvas[y-borderwidth:y + image.shape[0] + borderwidth, x - borderwidth:x + image.shape[1] + borderwidth] = bordercolor
    canvas[y:y + image.shape[0], x:x + image.shape[1]] = image


def drawX2(canvas, x, y, size, color):
    halfsize = int(size/2)
    for i in range(size):
        if y - halfsize + i >= 0 and y - halfsize + i < canvas.shape[0]:
            if x - halfsize + i >= 0 and x - halfsize + i < canvas.shape[1]:
                canvas[y - halfsize + i, x - halfsize + i] = color
            if x + halfsize - i >= 0 and x + halfsize - i < canvas.shape[1]:
                canvas[y - halfsize + i, x + halfsize - i] = color


def imageSavingLoop():
    index = 0
    SCALE_FACTOR = 4
    overlay = None

    while not saveImageQ.empty():
        saveImageQ.get()

    while True:
        data = saveImageQ.get()


        minimapRGB = data['minimapImage'].copy()
        minimapRGB = cv2.cvtColor(minimapRGB, cv2.COLOR_RGB2BGR)
        minimapRGB = cv2.resize(minimapRGB, dsize=(minimapRGB.shape[0]+1, minimapRGB.shape[1]+1), interpolation=cv2.INTER_NEAREST)
        newSize = applyScaleFactor(minimapRGB.shape, SCALE_FACTOR)
        minimapRGB = cv2.resize(minimapRGB, dsize=newSize, interpolation=cv2.INTER_NEAREST)

        if overlay is None:
            overlay = np.zeros(minimapRGB.shape)

        playerPos = applyScaleFactor(data['playerPos'], SCALE_FACTOR)

        drawX(overlay, playerPos, SCALE_FACTOR, (255, 255, 0))

        for enemyPos in data['enemies']:
            pos = applyScaleFactor(enemyPos, SCALE_FACTOR)
            drawX(overlay, pos, SCALE_FACTOR,  (0, 0, 255))

        
        nonzerooverlay = np.any(overlay > (10, 10, 10), axis=-1)
        minimapRGB[nonzerooverlay] = overlay[nonzerooverlay]

        currentDirection = getMostRecent(currentDirectionQForImage)
        unprocessedImage = cv2.cvtColor(vision.scaleDown(data['imageBeforeEdits']),cv2.COLOR_RGB2BGR)
        processedImage = data['hsvimage'].copy()
        if currentDirection:
            vision.isDirectionClear(processedImage, currentDirection, 50, directionToOrthogonal[currentDirection], debug=True)
        processedImage = cv2.cvtColor(processedImage,cv2.COLOR_HSV2BGR)
        enemyLoc = getEnemyLocAdjusted(data["enemyterritory"], currentDirection)
        if enemyLoc:
            drawX2(processedImage, enemyLoc[1], enemyLoc[0], 9, (0, 0, 255))

        minimapH, minimapW, dims = minimapRGB.shape
        processedH, processedW, _ = processedImage.shape
        unprocessedH, unprocessedW, _ = unprocessedImage.shape
        borderwidth = 1
        paddingH = int((minimapH - processedH - unprocessedH)/3)
        canvas = np.zeros((minimapH, minimapW + processedW + 2*borderwidth, dims))


        applyImageWithBorder(canvas, minimapRGB, 0, 0, 0)
        canvas[:, minimapW] = (255, 255, 255)
        applyImageWithBorder(canvas, unprocessedImage, minimapW + borderwidth, paddingH, 1)
        applyImageWithBorder(canvas, processedImage, minimapW + borderwidth, 2*paddingH + unprocessedH, 1)


        cv2.imwrite(f"minimap/img{index:06d}.png", minimapRGB)
        cv2.imwrite(f"combined/img{index:06d}.png", canvas)

        overlay = overlay * 0.8
        index += 1


def queueClearAndPut(Q, data):
    while not Q.empty():
        Q.get()
    Q.put(data)


def imageProcessingLoop():
    whenToPutOnLowPriority = time.time()
    whenToPutOnGraphical = time.time()
    whenToPutOnImageSaving = time.time()
    while True:
        data = vision.getAllTheData(getOGImage=SAVE_IMAGES)
        queueClearAndPut(highPriorityQ, data)

        if time.time() > whenToPutOnLowPriority:
            whenToPutOnLowPriority = time.time() + 0.3
            queueClearAndPut(lowPriorityQ, data)
        
        if graphicalQ.qsize() < 2 and time.time() > whenToPutOnGraphical:
            whenToPutOnGraphical = time.time() + 0.033
            queueClearAndPut(graphicalQ, data)

        if SAVE_IMAGES and time.time() > whenToPutOnImageSaving:
            whenToPutOnImageSaving = time.time() + 0.5
            saveImageQ.put(data)
            if saveImageQ.qsize() > 10:
                saveImageQ.get()

        time.sleep(0.004)




def stopCommand():
    print("putting exit events")
    eventQ.put(EXIT_EVENT)
    actionQ.put(EXIT_EVENT)


def startImageProcessingCommand():
    if not hasattr(startImageProcessingCommand, 'thread'):
        startImageProcessingCommand.thread = threading.Thread(target=imageProcessingLoop)
        startImageProcessingCommand.thread.start()

def startMovingCommand():
    if not hasattr(startMovingCommand, 'thread'):
        startMovingCommand.thread = threading.Thread(target=actionLoop)
        startMovingCommand.thread.start()


def startMousingCommand():
    if not hasattr(startMousingCommand, 'thread'):
        startMousingCommand.thread = threading.Thread(target=lowPriorityLoop)
        startMousingCommand.thread.start()


def startSaveImagesCommand():
    if SAVE_IMAGES and not hasattr(startSaveImagesCommand, 'thread'):
        startSaveImagesCommand.thread = threading.Thread(target=imageSavingLoop)
        startSaveImagesCommand.thread.start()


if __name__ == "__main__":
    startImageProcessingCommand()
    mygui = GUI(startMovingCommand, startMousingCommand, startSaveImagesCommand, graphicalQ)
    mygui.mainloop()


# reimplement find player pos
# make a boolean minimap to use to find nearest uncaptured
