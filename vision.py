import numpy as np
import cv2
import pyautogui
import math
from PIL import Image

DEBUG = False
SAVE_EVERY_IMAGE = False

SCREENGRABYOFFSET = 103
SHRINKFACTOR = 8


MINIMAP_POS = (824, 1807)
MINIWIDTH = 99

UPGRADE_DIMS = (195, 259)

MAXY = 96
MAXX = 96

ORIGINAL_BACKGROUND_RGB = (242, 247, 255)
UPGRADE_COLOR_RGB = (128, 128, 128)

ORIGINAL_BACKGROUND_HSV = (108, 13, 255)
GRIDLINE = (0, 0, 221)
TEMP = (0, 0, 0)


SPECTATE_BUTTON_COLOR = (149, 165, 166)
SPECTATE_BUTTON_HOVERED_COLOR = (121, 141, 143)

MINIMAP_PLAYER_COLOR = (255, 255, 255)
MINIMAP_ENEMY_COLOR = (128, 128, 128)
MINIMAP_TERRITORY_COLOR = (255, 138, 42)
MINIMAP_TERRITORY_OVERLAP_COLOR = (255, 206, 166)
MINIMAP_NOTHING_OVERLAP_COLOR = (179, 180, 181)

BACKGROUND_HSV = (0, 0, 0)
ENEMY_HSV = (255, 255, 200)
MINE_HSV = (15, 255, 255)
ENEMYARR = np.array(ENEMY_HSV)

UPGRADE_NAMES = ['Player speed', 'Bullet speed', 'Bullet range', 'Reload speed', 'Build  range', 'Tower shield', 'Tower health']

def scaleDown(image):
    return image[::SHRINKFACTOR, ::SHRINKFACTOR, :]


def highlight2(image):
    neutralterritory = np.logical_or(np.any(image < (0, 20, 0), axis=-1), np.all(image == GRIDLINE, axis=-1))
    myterritory = np.logical_and(np.any(image < (20, 0, 0), axis=-1), np.any(image > (6, 255, 255), axis=-1))
    enemyterritory = np.logical_and(np.logical_not(neutralterritory), np.logical_not(myterritory))

    image[neutralterritory] = BACKGROUND_HSV
    image[myterritory] = MINE_HSV
    image[enemyterritory] = ENEMY_HSV

    return myterritory, enemyterritory


def isRespawnMenuOpen(fullrgbimage):
    graycount = 0
    for y in range(60):
        if (fullrgbimage[491 + y, 931] == SPECTATE_BUTTON_COLOR).all() or (fullrgbimage[491 + y, 931] == SPECTATE_BUTTON_HOVERED_COLOR).all():
            graycount += 1
            if graycount > 10:
                return True
    return False


def isUpgradeMenuOpen(fullrgbimage):
    for y in range(5):
        if (fullrgbimage[721 + 26*y, 237] == UPGRADE_COLOR_RGB).all():
            return True
    return False


def getUpgradeStatus(fullrgbimage):
    upgradeStatus = {}
    for y in range(7):
        for x in range(8):
            # print(f"{y}, {x}, {(fullrgbimage[714 + 26*y, 237 + 28*x] == UPGRADE_COLOR_RGB)}")
            if (fullrgbimage[714 + 26*y, 31 + 28*x] == UPGRADE_COLOR_RGB).all():
                upgradeStatus[UPGRADE_NAMES[y]] = x
                break
        if UPGRADE_NAMES[y] not in upgradeStatus:
            upgradeStatus[UPGRADE_NAMES[y]] = 8

    return upgradeStatus


SELECT_SUPERPOWER_STRIPE = [(255,181,140), (225,44,37), (219,17,17), (212,8,8), (211,21,17), (242,131,102), (255,181,140), (255,181,140), (255,181,140), (255,181,140), (255,181,140), (255,181,140), (155,123,104), (14,141,175), (32,97,114), (46,63,67), (22,121,147), (47,59,63), (51,51,51), (39,79,90), (14,141,174), (32,96,112), (49,55,57), (43,74,82), (130,101,86), (254,181,140),]
def isSelectSuperpower(fullrgbimage):
    stripe = fullrgbimage[129, 986:1012]
    # for pixel in stripe:
    #     print(f"({pixel[0]},{pixel[1]},{pixel[2]}), ", end="")
    # print()
    return (stripe == SELECT_SUPERPOWER_STRIPE).all()


def getClosestNotTerritoryLoc(minimapTerritory, pos):
    h, w = minimapTerritory.shape
    centerx = pos[1]; centery = pos[0]
    closest = None
    closestDistance = 9999999
    for y in range(1, h-1):
        for x in range(1, w-1):
            if not minimapTerritory[y, x]:
                distance = (y-centery)*(y-centery) + (x-centerx)*(x-centerx)
                if distance < closestDistance:
                    closestDistance = distance
                    closest = (y, x)
    return closest


def processMinimap(minimapSection):

    playerIndices = np.all(minimapSection == MINIMAP_PLAYER_COLOR, axis=-1).nonzero()
    playerPos = (int(MAXY/2), int(MAXX/2))
    if len(playerIndices[0]) > 0:
        playerPos = (int(np.average(playerIndices[0])) - 1, int(np.average(playerIndices[1])) - 1)
    
    allEnemyPos = np.transpose(np.all(minimapSection == MINIMAP_ENEMY_COLOR, axis=-1).nonzero())
    enemyNearby = False
    allEnemyPos = set([(pos[0], pos[1]) for pos in allEnemyPos])
    validEnemyIndices = []
    for pos in allEnemyPos:
        distance = abs(pos[0] - playerPos[0]) + abs(pos[1] - playerPos[1])
        if abs(pos[0] - playerPos[0]) + abs(pos[1] - playerPos[1]) < 10 and (pos[0] != 96 and pos[1] != 96):
            enemyNearby = True
        neighbors = set([(pos[0] - 1, pos[1]), (pos[0] + 1, pos[1]), (pos[0], pos[1] - 1), (pos[0], pos[1] + 1)])
        if neighbors.issubset(allEnemyPos):
            validEnemyIndices.append((pos[0]-1, pos[1]-1))

    minimapSection = minimapSection[:-3, :-3]
    minimapSection[np.all(minimapSection == MINIMAP_TERRITORY_OVERLAP_COLOR, axis=-1)] = MINIMAP_TERRITORY_COLOR
    minimapSection[np.logical_and(np.any(minimapSection != MINIMAP_PLAYER_COLOR, axis=-1), np.any(minimapSection != MINIMAP_TERRITORY_COLOR, axis=-1))] = (0, 0, 0)
    if not hasattr(processMinimap, 'previousMinimap'):
        minimapSection[np.all(minimapSection == MINIMAP_PLAYER_COLOR, axis=-1)] = MINIMAP_TERRITORY_COLOR
    else:
        playerCells = np.all(minimapSection == MINIMAP_PLAYER_COLOR, axis=-1)
        minimapSection[playerCells] = processMinimap.previousMinimap[playerCells]
        enemyCells = np.all(minimapSection == MINIMAP_ENEMY_COLOR, axis=-1)
        minimapSection[enemyCells] = processMinimap.previousMinimap[enemyCells]

    myterritory = np.logical_or(np.all(minimapSection == MINIMAP_TERRITORY_COLOR, axis=-1), np.all(minimapSection == MINIMAP_PLAYER_COLOR, axis=-1))
    closestNotTerritory = getClosestNotTerritoryLoc(myterritory, playerPos)

    minimapSection[myterritory] = (255, 255, 255)
    processMinimap.previousMinimap = minimapSection
    return minimapSection, myterritory, playerPos, validEnemyIndices, enemyNearby, closestNotTerritory


def getAllTheData(getOGImage=False, getMinimap=True, getUpgrades=True, getSelectSuperpower=True, getRespawn=True, getUnprocessedMinimap=False):
    ogimage = np.array(pyautogui.screenshot())
    ogimage = ogimage[SCREENGRABYOFFSET:-40, :, :]
    dataDict = {}

    if getOGImage:
        dataDict["imageBeforeEdits"] = ogimage.copy()
        
    if getRespawn:
        if isRespawnMenuOpen(ogimage):
            dataDict["respawnmenu"] = True

    if getMinimap:
        minimap = ogimage[MINIMAP_POS[0]:MINIMAP_POS[0]+MINIWIDTH, MINIMAP_POS[1]:MINIMAP_POS[1]+MINIWIDTH, :]
        if getUnprocessedMinimap:
            dataDict["unprocessedminimap"] = np.copy(minimap)
        dataDict["minimapImage"], dataDict["minimapTerritory"], dataDict["playerPos"], dataDict["enemies"], dataDict['enemyNearby'], dataDict['closestNotTerritory'] = processMinimap(np.copy(minimap))

    if getUpgrades and isUpgradeMenuOpen(ogimage):
        dataDict["upgrades"] = getUpgradeStatus(ogimage)
        ogimage[694:694+195, 16:16+260] = ORIGINAL_BACKGROUND_RGB
    
    if getSelectSuperpower:
        if isSelectSuperpower(ogimage):
            dataDict["selectsuperpower"] = True
    

    # removes minimap darkening
    # ogimage[MINIMAP_POS[0]-1:MINIMAP_POS[0]+MINIWIDTH+1, MINIMAP_POS[1]-1:MINIMAP_POS[1]+MINIWIDTH+1] = ogimage[MINIMAP_POS[0]-1:MINIMAP_POS[0]+MINIWIDTH+1, MINIMAP_POS[1]-1:MINIMAP_POS[1]+MINIWIDTH+1]*3.38 - 2
    ogimage[MINIMAP_POS[0]-1:MINIMAP_POS[0]+MINIWIDTH+1, MINIMAP_POS[1]-1:MINIMAP_POS[1]+MINIWIDTH+1] = ORIGINAL_BACKGROUND_RGB
    # server debug string
    ogimage[908:908+13, 16:16+260] = ORIGINAL_BACKGROUND_RGB
    # leaderboard
    ogimage[16:280, 1640:1904] = ORIGINAL_BACKGROUND_RGB
    # player
    ogimage[445:492, 936:984] = ORIGINAL_BACKGROUND_RGB
    # cant build dot on existing line
    ogimage[55:84, 830:1090] = ORIGINAL_BACKGROUND_RGB

    
    dataDict["rgbimage"] = ogimage
    small = scaleDown(ogimage)
    if DEBUG:
        dataDict["reducedSize"] = small
    hsvimage = cv2.cvtColor(small,cv2.COLOR_RGB2HSV)
    
    if DEBUG:
        dataDict["smallhsvimage"] = hsvimage.copy()
    myterritory, enemyterritory = highlight2(hsvimage)

    numMyTerritory = np.count_nonzero(myterritory)
    percentMine = 100*numMyTerritory / (myterritory.shape[0] * myterritory.shape[1])
    numEnemyTerritory = np.count_nonzero(enemyterritory)
    percentEnemy = 100*numEnemyTerritory / (enemyterritory.shape[0] * enemyterritory.shape[1])

    dataDict["hsvimage"] = hsvimage
    dataDict["myterritory"] = myterritory
    dataDict["enemyterritory"] = enemyterritory
    dataDict["percentmyterritory"] = percentMine
    dataDict["percentenemyterritory"] = percentEnemy
    return dataDict


def grabScreen():
    ogimage = pyautogui.screenshot()
    image = cv2.cvtColor(np.array(ogimage), cv2.COLOR_RGB2BGR)
    image = image[SCREENGRABYOFFSET:-40, :, :]
    hsvimage = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
    minimap = image[824:824+MINIWIDTH, 1807:1807+MINIWIDTH, :]    
    return (image, minimap, hsvimage)


def isDefeatedScreen(hsvimage):
    spectateButton = hsvimage[491:491+30, 890:890+95, :]
    avg = np.average(spectateButton, axis = (0, 1))
    # 84.43333333  57.7877193  161.14491228
    if DEBUG: print(avg)
    return (77 < avg[0] < 97) and (13 < avg[1] < 67) and (151 < avg[2] < 185)


def isUpgradeScreen(hsvimage):
    # 19 712 222 175
    upgradeArea = hsvimage[712:712+175, 19:19+222, :]
    if DEBUG:
        cv2.imwrite("upgrade.png", cv2.cvtColor(upgradeArea,cv2.COLOR_HSV2BGR))
    for i in range(4):
        y = 29 + 26*i
        block = upgradeArea[y:y+12, 171:171+20]
        avg = np.average(block, axis = (0, 1))
        if DEBUG:
            print(f"avg of block {i} = {avg}")
        if (avg[0] < 5) and (avg[1] < 5) and (125 < avg[2] < 132):
            return True
    return False


def isChooseAbilityScreen(hsvimage):
    area1 = hsvimage[100:108, 719:728, :]
    avg1 = np.average(area1, axis = (0, 1))
    area2 = hsvimage[112:112+22, 1023:1023+13, :]
    avg2 = np.average(area2, axis = (0, 1))
    if DEBUG:
        print(f"area1 avg1: {avg1}, avg2: {avg2}")
    return (9 < avg2[0] < 13) and (113 < avg2[1] < 117) and (253 < avg2[2]) and (90 < avg1[0] < 105) and (245 < avg1[1]) and (160 < avg1[2] < 180)


def _abilityreadyhelper(area):
    avg = np.average(area, axis = (0, 1))
    if DEBUG:
        print(f"ability cd area avg: {avg}")
    isbarfull = not ((avg[0] < 5) and (avg[1] < 5) and (140 < avg[2] < 150))
    isbarorange = (13 < avg[0] < 17) and (200 < avg[1]) and (250 < avg[2])
    return isbarfull and isbarorange

def isAbilityReady(hsvimage):
    area1 = hsvimage[846:846+14, 1245:1245+2, :]
    area1ready = _abilityreadyhelper(area1)
    area2 = hsvimage[868:868+18, 1244:1244+2, :]
    area2ready = _abilityreadyhelper(area2)
    return area1ready or area2ready
    

def maskUI(image):
    y = int(image.shape[0]/2)
    x = int(image.shape[1]/2)
    image = image[y-384:y+384, x-600:x+600]
    return image


def findPlayer(minimap):
    for y in range(minimap.shape[0] - 2):
        for x in range(minimap.shape[1] - 2):
            success = True
            for p in [minimap[y][x+1], minimap[y+1][x], minimap[y+1][x+1], minimap[y+1][x+2], minimap[y+2][x+1]]:
                if not (p == (255, 255, 255)).all():
                    success = False
            if success:
                return (y, x)
    return (55, 55)



def isOrange(pixel):
    return pixel[0]*4 < pixel[1]*2 < pixel[2]


def highlight(image):
    h = image.shape[0]
    w = image.shape[1]
    # print(image[int(h/2), :])
    off = 3
    image[np.all(image <= (360, 20, 255), axis=-1)] = ORIGINAL_BACKGROUND_HSV
    image[np.all(image == GRIDLINE, axis=-1)] = ORIGINAL_BACKGROUND_HSV
    image[np.all(image == ORIGINAL_BACKGROUND_HSV, axis=-1)] = TEMP
    image[np.all(image > (20, 0, 0), axis=-1)] = ENEMY_HSV
    image[np.all(image == TEMP, axis=-1)] = ORIGINAL_BACKGROUND_HSV
    image[np.all(image < (6, 255, 255), axis=-1)] = ENEMY_HSV
    image[np.all(image == TEMP, axis=-1)] = ORIGINAL_BACKGROUND_HSV
    image[np.all(image <= (20, 255, 255), axis=-1)] = MINE_HSV
    image[int(h/2-off):int(h/2+off+1), int(w/2-off):int(w/2+off+1)] = MINE_HSV


def getHighlightedImage():
    image, minimap, hsvimage = grabScreen()
    isdefeated = isDefeatedScreen(hsvimage)
    isupgrade = isUpgradeScreen(hsvimage)
    isability = isUpgradeScreen(hsvimage)
    isabilityready = isAbilityReady(hsvimage)
    position = findPlayer(minimap)
    hsvimage = maskUI(hsvimage)
    small = scaleDown(hsvimage)
    highlight(small)
    return small, position, isdefeated, isupgrade, isability, isabilityready

def isDirectionClear(highlighted, direction, distance, orthogonal, debug=DEBUG):
    h = highlighted.shape[0]
    w = highlighted.shape[1]
    x = int(w/2)
    y = int(h/2)

    isDiagonal = orthogonal[0] != 0 and orthogonal[1] != 0
    conegrowth = 16 if isDiagonal else 16

    if isDiagonal:
        distance = int(distance*3/4)

    for i in range(distance):
        ratio = i / distance
        x += direction[1]
        y += direction[0]
        if not (x < 0 or y < 0 or x >= w or y >= h):
            if debug: highlighted[y, x, 1:] = (highlighted[y, x, 1:] + [0, 255])/2
            if (highlighted[y, x] == ENEMYARR).all():
                return i, 0

        for mult in range(1, 8 + int(ratio*conegrowth)):
            xx = x + mult*orthogonal[1]
            yy = y + mult*orthogonal[0]
            if not (xx < 0 or yy < 0 or xx >= w or yy >= h):
                if debug: highlighted[yy, xx, 1:] = (highlighted[yy, xx, 1:] + [0, 255])/2
                if (highlighted[yy, xx] == ENEMYARR).all():
                    return i, mult
            xx = x - mult*orthogonal[1]
            yy = y - mult*orthogonal[0]
            if not (xx < 0 or yy < 0 or xx >= w or yy >= h):
                if debug: highlighted[yy, xx, 1:] = (highlighted[yy, xx, 1:] + [0, 255])/2
                if (highlighted[yy, xx] == ENEMYARR).all():
                    return i, -mult

    return 999, 0


def getClosestEnemyLoc(enemyterritory):
    h, w = enemyterritory.shape
    centerx = int(w/2); centery = int(h/2)
    closest = None
    closestDistance = 9999999
    for y in range(h):
        for x in range(w):
            if enemyterritory[y, x]:
                distance = (y-centery)*(y-centery) + (x-centerx)*(x-centerx)
                if distance < closestDistance:
                    closestDistance = distance
                    closest = (y, x)
    return closest



if __name__ == "__main__":
    DEBUG = True
    SAVE_EVERY_IMAGE = True
    image, minimap, hsvimage = grabScreen()
    position = findPlayer(minimap)
    print(f"Player at: {position}")


    print(f"isdefeated: {isDefeatedScreen(hsvimage)}")
    print(f"isupgrade: {isUpgradeScreen(hsvimage)}")
    print(f"isability: {isChooseAbilityScreen(hsvimage)}")
    print(f"isAbilityReady: {isAbilityReady(hsvimage)}")

    print(f"520, 407: rgb: {image[407, 520]}, hsv: {hsvimage[407, 520]}")

    # writing it to the disk using opencv
    cv2.imwrite("image1.png", image)

    cv2.imwrite("minimap.png", minimap)

    hsvimage = maskUI(hsvimage)
    small = scaleDown(hsvimage)
    cv2.imwrite("small.png", cv2.cvtColor(small,cv2.COLOR_HSV2BGR))

    highlight(small)


    clear = isDirectionClear(small, (1, 1), 60, (1, -1))
    clear = isDirectionClear(small, (0, -1), 60, (1, 0))
    print(f"isDirectionClear: {clear}")

    cv2.imwrite("highlight.png", cv2.cvtColor(small,cv2.COLOR_HSV2BGR))



    data = getAllTheData(getOGImage=True, getUnprocessedMinimap=True)
    print(f"minimap: {data['minimapImage'].shape}")
    print(f"unprocessedminimap: {data['unprocessedminimap'].shape}")
    print(f"hsvimage: {data['hsvimage'].shape}")

    print(f"max value: {np.max(data['hsvimage'])}")
    cv2.imwrite("minimap2.png", cv2.cvtColor(data['minimapImage'], cv2.COLOR_RGB2BGR))
    cv2.imwrite("unprocessedminimap.png", cv2.cvtColor(data['unprocessedminimap'], cv2.COLOR_RGB2BGR))
    cv2.imwrite("rgbimage.png", cv2.cvtColor(data['rgbimage'], cv2.COLOR_RGB2BGR))
    cv2.imwrite("highlight2.png", cv2.cvtColor(data['hsvimage'], cv2.COLOR_HSV2BGR))

    for key in data:
        try:
            conversion = cv2.COLOR_HSV2BGR if 'hsv' in key else cv2.COLOR_RGB2BGR
            cv2.imwrite(f"debugimages/{key}.png", cv2.cvtColor(data[key], conversion))
        except:
            print(f"{key}: {data[key]}")
