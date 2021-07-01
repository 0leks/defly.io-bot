# Automating defly.io

https://user-images.githubusercontent.com/1296131/124110163-cf7dce00-da1c-11eb-98b8-a7f0a1ec5e5b.mp4

# About the game
In defly.io, the you take control of a drone to fly around and capture territory by surrounding it with nodes and walls. Pressing space will drop a node that automatically connects a wall to the previous node. Once you complete a loop, the interior is filled in with your color and you gain some points proportional to the size of the area captured. As you gain points your drone will level up and allow you to choose from 7 different upgrades. When you encounter enemy drones you can break their territory by shooting at their nodes or by using special abilities that are unlocked at level 18. 


# Motivation
99% of the "players" one encounters in defly.io are bots included to make the game seem active to people that try it out. These bots are quite bad and struggle to accomplish much more than not flying into enemy walls. I want to make a better bot that uses simple decision making.


# Image processing 

## Game view

### 0. Raw Game View

![imagebeforeedits.png](/technical/deflyio/imagebeforeedits.png)

### 1. Cover the UI

![rgbimage.png](/technical/deflyio/rgbimage.png)

> Replace UI areas with the background color.
This includes the scoreboard, minimap, upgrade menu, the player's drone, and the area where some status messages show up in red.
{.is-info}

### 2. Downscale

![reducedsize.png](/technical/deflyio/reducedsize.png)

> Scale down the image by a factor of 8, keeping 1 of every 64 pixels. This reduces the image size from `1920x937` to `240x118`
Notice that the purple bullet still shows up as a few pixels. This is important for the bot to be able to avoid enemy bullets.
{.is-info}

### 3. Detect Friendly/Enemy/Neutral

![hsvimage.png](/technical/deflyio/hsvimage.png)

> Convert to HSV and detect ownership of each pixel:
→ *_saturation_ < 20* is background
→ *6 < _hue_ < 20* is friendly territory or walls (orange)
→ anything else is enemy territory or walls (these pixels aren't orange but they are colorful enough to not be background)
{.is-info}


## Minimap view

Processing the minimap is fairly simple.
1. The orange pixels are my territory.
2. The pure white (255, 255, 255) plus sign is me.
3. Grey plus signs (128, 128, 128) are enemy drones.
4. Everything else is background

Remarks:
- The size of the map is 250x250 squares but the minimap is only 96x96 pixels so each pixel on the minimap corresponds to approximately 2.5 squares on the map.
- The actual position of the player is closer to the top left corner of the bounding box of the plus sign, not the center. It seems like the game developers were a little bit lazy and didn't spend the extra effort to center the plus marker around the players actual position.

![unprocessedminimap.png](/technical/deflyio/unprocessedminimap.png) ![minimapimage.png](/technical/deflyio/minimapimage.png)

## Upgrades

Discovering which upgrades the player has unlocked is a trivial task. 
It is sufficient to querying a pixel near the top of each cell in the table and check if it is orange.
Below is an example with 1 level in "Player speed" and nothing else.  
![upgrades.png](/technical/deflyio/upgrades.png)

# AI

## Controls
Move in 8 different directions using combinations of W A S D
Move the mouse cursor and click to shoot.
Press E to use special ability.
Press 1-7 to choose upgrades.


## Basic motion
The bot is governed by 2 very simple rules. 
1. Upon seeing an enemy pixel ahead, turn clockwise. 
2. After not seeing an enemy pixel in a while, turn counterclockwise.

These two rules alone result in decent performance as the bot is good at surviving but not very efficient at capturing territory. 

## Motion efficiency tricks
A few tricks help the bot by making it more greedy when it is safe

3. When moving into edge of the map based on minimap player location of 0 or 96, turn clockwise
4. When there are no enemies nearby showing on the minimap, approach enemy pixels closer before turning away.
5. If there are no enemies nearby and there is no enemy territory visible and 40% of the screen is friendly territory, redirect movement towards the nearest non-captured area according to the minimap.

## Offense

The bot always moves the mouse cursor onto the nearest enemy pixel and periodically clicks and presses E to throw grenade.
Even though this strategy is not focused and results in lots of misses, it will slowly chip away at enemy territory. 

### Using the grenade to blow stuff up

https://user-images.githubusercontent.com/1296131/124110275-e8867f00-da1c-11eb-83d3-45a704165117.mp4



