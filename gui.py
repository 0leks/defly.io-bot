import numpy as np
import tkinter as tk
import cv2
from PIL import Image, ImageTk
import threading


import vision


MINIMAP_VIEW_SIZE = (vision.MAXX + 2)*4


def makeImageCanvas(parent, width, height, title=None):
    frame = tk.Frame(parent, borderwidth = 0, highlightbackground = "black")
    if title is not None:
        label = tk.Label(frame, text=title)
        label.pack(side=tk.TOP)
    canvas = tk.Canvas(frame, width=width, height=height, borderwidth = 0)
    canvas.pack(side=tk.BOTTOM)
    return frame, canvas


def replaceCanvasImage(canvasdata, image, targetsize):
    # canvasdata[0] is the canvas
    # canvasdata[1] is the canvasImage
    # canvasdata[2] is the currentImage
    img = Image.fromarray(image)
    img = img.resize(targetsize, Image.NEAREST)
    img = ImageTk.PhotoImage(image=img)
    if canvasdata[1] is None:
        canvasdata[1] = canvasdata[0].create_image(2, 2, anchor="nw", image=img) 
    else:
        canvasdata[0].itemconfig(canvasdata[1], image = img)
    canvasdata[2] = img


class GUI:
    def __init__(self, startMovingCommand, startMousingCommand, startSaveImagesCommand, graphicalQ):
        self.graphicalQ = graphicalQ
        self.root = tk.Tk()

        buttonFrame = tk.Frame(self.root)
        buttonFrame.pack()

        infoFrame = tk.Frame(self.root)
        infoFrame.pack()

        infoFrameBottom = tk.Frame(self.root)
        infoFrameBottom.pack()

        startSaveImageButton = tk.Button(buttonFrame, width=14, height=2, text="StartSaveImages", command = lambda: startSaveImagesCommand() or startSaveImageButton.pack_forget())
        startMousingButton = tk.Button(buttonFrame, width=10, height=2, text="StartMouse", command = lambda: startMousingCommand() or startMousingButton.pack_forget())
        startMoveButton = tk.Button(buttonFrame, width=10, height=2, text="StartMove", command = lambda: startMovingCommand() or startMoveButton.pack_forget())

        startAllCommand = lambda : startMovingCommand() or startMousingCommand() or startMoveButton.pack_forget() or startMousingButton.pack_forget()
        startAllButton = tk.Button(buttonFrame, width=14, height=2, text="StartMove&Mouse", command = lambda: startAllCommand() or startAllButton.pack_forget())

        startSaveImageButton.pack(side=tk.RIGHT)
        startAllButton.pack(side=tk.RIGHT)
        startMousingButton.pack(side=tk.RIGHT)
        startMoveButton.pack(side=tk.RIGHT)

        minimapFrame, self.minimapCanvas = makeImageCanvas(infoFrame, width=MINIMAP_VIEW_SIZE, height=MINIMAP_VIEW_SIZE, title="minimap")
        minimapFrame.pack(side = tk.LEFT)
        self.minimapSquares = {}

        INPUT_IMAGE_DIMS = (240, 118)
        self.DISPLAY_DIMS = (700, int(INPUT_IMAGE_DIMS[1] * 700 / INPUT_IMAGE_DIMS[0]))
        
        gameFrame, self.gameCanvas = makeImageCanvas(infoFrame, width=self.DISPLAY_DIMS[0],height=self.DISPLAY_DIMS[1], title="game")
        gameFrame.pack(side=tk.RIGHT)

        self.upgradeText = tk.Text(buttonFrame, height=8, width=20)
        self.upgradeText.pack(side=tk.LEFT, padx=10)
        
        self.infoText = tk.Text(buttonFrame, height=8, width=36)
        self.infoText.pack(side=tk.LEFT, padx=10)


    def drawSquareOnMinimap(self, pos, key, color):
        drawy = 2 + int(pos[0]*(MINIMAP_VIEW_SIZE + 1)/(vision.MAXY+1))
        drawx = 2 + int(pos[1]*(MINIMAP_VIEW_SIZE + 1)/(vision.MAXX+1))
        draww = MINIMAP_VIEW_SIZE / (vision.MAXY+1)
        if key not in self.minimapSquares:
            self.minimapSquares[key] = self.minimapCanvas.create_rectangle(drawx, drawy, drawx+draww, drawy+draww, fill=color, width=0)
        else:
            self.minimapCanvas.coords(self.minimapSquares[key], (drawx, drawy, drawx+draww, drawy+draww))


    def updateLoop(self, canvas, minimapCanvas, upgradeText, infoText):
        gamedata = [canvas, None, None]
        minimapdata = [minimapCanvas, None, None]
        previousUpgradeString = None
        previousInfoString = None

        canvasimage = None
        canvasMinimapImage = None
        previousImage = None
        previousMinimapImage = None
        END = False
        try:
            while not END:
                dataDict = self.graphicalQ.get()
                playerPos = dataDict['playerPos']

                highlighted = dataDict["hsvimage"]
                rgbimage = cv2.cvtColor(highlighted,cv2.COLOR_HSV2RGB)
                replaceCanvasImage(gamedata, rgbimage, self.DISPLAY_DIMS)

                minimapImage = dataDict["minimapImage"]
                replaceCanvasImage(minimapdata, minimapImage, (MINIMAP_VIEW_SIZE, MINIMAP_VIEW_SIZE))
                self.drawSquareOnMinimap(dataDict['closestNotTerritory'], "notterritory", "#F00")
                self.drawSquareOnMinimap(playerPos, "player", "#0FF")

                if "upgrades" in dataDict:
                    upgrades = dataDict["upgrades"]
                    upgradestring = '\n'.join(['upgrades'] + [f"{key}:\t{upgrades[key]}/8" for key in upgrades])
                    if upgradestring != previousUpgradeString:
                        upgradeText.delete("1.0", tk.END)
                        upgradeText.insert(tk.END, upgradestring)
                        previousUpgradeString = upgradestring

                infoString = ""
                if "respawnmenu" in dataDict:
                    infoString += f"respawn menu = {dataDict['respawnmenu']}\n"
                
                if "selectsuperpower" in dataDict:
                    infoString += f"select superpower = {dataDict['selectsuperpower']}\n"

                infoString += f"{dataDict['percentmyterritory']:.0f}% of view is my territory\n"
                infoString += f"{dataDict['percentenemyterritory']:.0f}% of view is enemy territory\n"
                infoString += f"player pos: {playerPos}\n"
                infoString += f"enemies: {dataDict['enemies']}\n"
                infoString += f"enemy nearby: {dataDict['enemyNearby']}\n"
                infoString += f"closest not territory: {dataDict['closestNotTerritory']}\n"


                if infoString != previousInfoString:
                    infoText.delete("1.0", tk.END)
                    infoText.insert(tk.END, infoString)
                    previousInfoString = infoString
        finally:
            print("exiting updateLoop")


    def mainloop(self):
        thread = threading.Thread(target=self.updateLoop, args=(self.gameCanvas, self.minimapCanvas, self.upgradeText, self.infoText))
        thread.start()
        self.root.mainloop()
