import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame, xml.etree.ElementTree as ET, math, sys
pygame.mixer.init()
pygame.font.init()
WIDTH = 640
HEIGHT = 480
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED|pygame.RESIZABLE, vsync=1)
icon = pygame.image.load("assets/global/icon.png").convert_alpha()
pygame.display.set_caption("Attempt 2")
pygame.display.set_icon(icon)
clock = pygame.time.Clock()

TILESIZE = 40
FPS = 60
FADE_O = 255 #opaque
FADE_T = 0 #transparent
PLAYERS = 4

def loadimg(img):
    return pygame.image.load(img).convert_alpha()

img_obj = loadimg('assets/global/objects.png')
img_flag = loadimg('assets/global/flags.png')

snd_spring = pygame.mixer.Sound('assets/global/sfx/spring.mp3')
snd_die = pygame.mixer.Sound('assets/global/sfx/death.mp3')
snd_fall = pygame.mixer.Sound('assets/global/sfx/fall.mp3')

def ease(t):
    return 1 - ((1 - t) ** 3)

#objects
class Spring:
    def __init__(self, x, y):
        self.pos = (int(x), int(y))
        self.spritesheet = img_obj
        self.image_unboing = (0, 0, TILESIZE, TILESIZE)
        self.image_boing = (TILESIZE, 0, TILESIZE, TILESIZE)
        self.sprite = self.image_unboing
        self.activateTimer = 0
        self.imageRect = pygame.Rect(self.pos[0], self.pos[1]+(TILESIZE-25), TILESIZE, 25) #25 is the height of the spring image
        self.prevPlayer = None

    def collide(self, object):
        if self.imageRect.colliderect(object.rect):
            object.yVel = -15
            object.jumps[1] = 1
            self.activateTimer = 30


    def update(self, player):
        global playerList

        if self.activateTimer > 0:
            self.activateTimer -= 1
            self.sprite = self.image_boing
        else:
            self.sprite = self.image_unboing

        if self.activateTimer == 28:
            snd_spring.play()

        player.camera.blit(self.spritesheet, dest=(player.cameraPos[0]+self.pos[0], player.cameraPos[1]+self.pos[1]+1), area=self.sprite)
        self.collide(player)
        
class Goal:
    def __init__(self, x, y, type):
        self.type = type
        self.pos = (int(x), int(y)-TILESIZE/2)
        self.rect = pygame.Rect(self.pos[0], self.pos[1], TILESIZE, TILESIZE*1.5)
        if type == 'normal':
            self.sprite = (0, 0, TILESIZE, TILESIZE*1.5)
        elif type == 'secret':
            self.sprite = (TILESIZE, 0, TILESIZE, TILESIZE*1.5)
        self.spritesheet = img_flag
        self.frame = 0
        self.anim = 0

    def collide(self, player):
        if self.rect.colliderect(player.rect):
            player.win(self.type)

    def update(self, player):
        player.camera.blit(self.spritesheet, dest=(player.cameraPos[0]+self.pos[0], player.cameraPos[1]+self.pos[1]+1), area=(self.sprite[0], self.frame*(TILESIZE*1.5), self.sprite[2], self.sprite[3]))
        self.collide(player)
        self.anim += 1
        if self.anim > 59:
            self.anim = 0
        self.frame = math.floor(self.anim/20)

#not objects
class Tile:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x*TILESIZE, y*TILESIZE, TILESIZE, TILESIZE)
    
    def collide(self, object, direction):
        if direction == 'x':
            colliding = self.rect.colliderect(object.rect)
            if object.xVel <= 0:
                changeX = 0.5
            elif object.xVel > 0:
                changeX = -0.5

            while colliding:
                object.changePos(changeX, 0)
                object.xVel = 0
                colliding = self.rect.colliderect(object.rect)

        elif direction == 'y':
            colliding = self.rect.colliderect(object.rect)
            if object.yVel < 0:
                changeY = 1
            elif object.yVel > 0:
                changeY = -1
            while colliding:
                if changeY == -1:
                    object.jumps[1] = object.jumps[0]
                    object.coyoteTime = 8
                object.changePos(0, changeY)
                object.yVel = 0
                colliding = self.rect.colliderect(object.rect)

class Map:
    def __init__(self, folder):
        self.path = folder
        self.spritesheet = loadimg(f'{folder}/tileset.png')
        self.bg = loadimg(f'{folder}/bg.png')
        self.mus = pygame.mixer.Sound(f'{folder}/mus.mp3')
        self.map = []
        self.parsetmx(folder)
        self.loadObjects()
        self.tiles = self.map
        self.draw()

        self.mus.play(loops=-1)

    def loadObjects(self):
        tempObjects = self.objects
        self.objects = []
        exit, secretexit = False, False
        for object in tempObjects:
            x, y, name = object.attrib['x'], object.attrib['y'], object.attrib['name']
            if name == 'spring':
                self.objects.append(Spring(x, y))
            elif name == 'exit' and exit == False:
                self.objects.append(Goal(x, y, 'normal'))
                exit == True
            elif name == 'secretexit' and secretexit == False:
                self.objects.append(Goal(x, y, 'secret'))
                secretexit == True

    def parsetmx(self, folder): #i put it in a function because its ugly
        tree = ET.parse(f'{folder}/map.tmx')
        root = tree.getroot()
        mapstr = root[1][0].text
        self.objects = root[2]
        for object in self.objects:
            if object.attrib['name'] == 'spawn':
                self.spawnPos = (int(object.attrib['x']), int(object.attrib['y']))
                break

        tempMap = mapstr.split("\n")
        for row in tempMap:
            self.map.append(row.split(","))
        self.map.pop(0)
        self.map.pop()
        for row in range(len(self.map)-1):
            self.map[row].pop()

    def draw(self):
        self.mapsurf = pygame.Surface(( TILESIZE*len(self.map[0]), TILESIZE*len(self.map) ), pygame.SRCALPHA) #tilesize is 40 and im not changing that
        self.mapsurf.convert_alpha()
        x, y = -1, -1
        for row in self.map:
            y += 1
            x = -1
            for tile in row:
                tile = int(tile)
                x += 1
                if tile != 0:
                    self.mapsurf.blit(self.spritesheet, dest=(x*TILESIZE, y*TILESIZE), area=(((tile-1)%5)*TILESIZE, math.floor((tile-1)/5)*TILESIZE, TILESIZE, TILESIZE))
                    self.tiles[y][x] = Tile(x, y)
                else:
                    self.tiles[y][x] = None

    def drawBG(self, player):
        player.camera.blit(self.bg, dest=((player.cameraPos[0]/4)%640-640, 0))
        player.camera.blit(self.bg, dest=((player.cameraPos[0]/4)%640, 0))
                    
    def update(self, player):
        self.drawBG(player)
        player.camera.blit(self.mapsurf, dest=player.cameraPos)
        for object in self.objects:
            object.update(player)


class Player:
    def __init__(self, controls):
        self.reset()
        self.camera = pygame.Surface((WIDTH, HEIGHT))
        self.fadeLayer = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
        self.fadeLayer.fill((0,0,0,255))
        self.fadeLayer.set_alpha(0)
        self.controls = []
        for button in controls:
            self.controls.append([button, False])

    def reset(self):
        global currentMap
        self.size = 30
        self.jumps = [2, 1]
        self.deathTimer = 0
        self.offsetX = 0
        self.offsetY = 0
        self.rect = pygame.Rect(currentMap.spawnPos[0], currentMap.spawnPos[1]+10, self.size, self.size)
        self.cameraPos = (-currentMap.spawnPos[0]+(WIDTH/2-20), -currentMap.spawnPos[1]+(HEIGHT/2-20))
        self.xVel = 0
        self.yVel = 0
        self.grav = 1
        self.speed = 5
        self.grav = 1
        self.speed = 5
        self.coyoteTime = 0
        self.won = False
        self.fadeTime = 0
        self.fadeStart, self.fadeEnd = FADE_O, FADE_T

    def setPos(self, x, y):
        self.rect = pygame.Rect(x, y, self.size, self.size)

    def changePos(self, x, y):
        self.rect = (self.rect[0] + x, self.rect[1] + y, self.size, self.size)

    def debug_drawRect(self):
        global playerList
        tempRect = (int(self.rect[0]-self.offsetX-currentMap.spawnPos[0]+(WIDTH/2-20)), int(self.rect[1]-math.floor(self.offsetY)-currentMap.spawnPos[1]+(HEIGHT/2-20)), self.size, self.size)
        pygame.draw.rect(self.camera, (255, 0, 0), tempRect)

        for player in playerList:
            if player != self:
                tempRect = (int(player.rect[0]-int(self.offsetX)-currentMap.spawnPos[0]+(WIDTH/2-20)), int(player.rect[1]-int(self.offsetY)-currentMap.spawnPos[1]+(HEIGHT/2-20)), player.size, player.size)
                pygame.draw.rect(self.camera, (255, 0, 0), tempRect)

    def win(self, exitType):
        global playerList
        if self.won == False:
            self.setFadeVars(FADE_T, FADE_O)
        self.won = exitType
        allWon = True
        for player in playerList:
            if player.won == False:
                allWon = False
        if self.fadeTime >= 2:
            self.setFadeVars(FADE_O, FADE_T)
            if len(playerList) == 1:
                currentMap.mus.stop()
                currentMap.mus.play()
            self.reset()
            self.allWon = False

    def die(self, deathType):
        global playerList
        if len(playerList) == 1:
            currentMap.mus.stop()
        if self.deathTimer == 0:
            self.setFadeVars(FADE_T, FADE_O)
            self.fadeTime = 0
            if deathType == 'spike':
                snd_die.stop()
                snd_die.play()
            elif deathType == 'fell':
                snd_fall.stop()
                snd_fall.play()
            self.deathTimer = FPS
        self.deathTimer -= 1
        if self.deathTimer == 0:
            if len(playerList) == 1:
                currentMap.mus.play()
            tempControls = []
            for button in self.controls:
                tempControls.append(button[0])
                self.reset()

    def jump(self):
        if self.yVel < 0:
            jumpMultiplier = (1+abs(self.yVel)/15)
        else:
            jumpMultiplier = 1
        self.yVel = -self.grav*10*jumpMultiplier

    def setFadeVars(self, start, end):
        self.fadeTime = 0
        self.fadeStart, self.fadeEnd = start, end

    def fade(self):
        self.fadeLayer.set_alpha(pygame.math.lerp(self.fadeStart, self.fadeEnd, ease(self.fadeTime)))
        self.fadeTime += 1/FPS*2


    def move(self):
        global currentMap, playerList
        pressedKeys = checkKeypress(self.controls)
        if pressedKeys[1]:
            self.facing = 0
            self.xVel -= self.speed/6
        elif pressedKeys[3]:
            self.facing = 1
            self.xVel += self.speed/6

        self.xVel *= 0.9

        if abs(self.xVel) < 0.05:
            self.xVel = 0
        self.changePos(self.xVel, 0)

        nearbyTiles = self.getNearbyTiles()
        for tile in nearbyTiles:
            tile.collide(self, 'x')

        if self.rect[0] < 0:
            self.rect = pygame.Rect(0, self.rect[1], self.rect[2], self.rect[3])
            self.xVel = 0

        if self.rect[0]+self.size > len(currentMap.map[0])*TILESIZE:
            self.rect = pygame.Rect((len(currentMap.map[0]))*TILESIZE-self.size, self.rect[1], self.rect[2], self.rect[3])
            self.xVel = 0

        self.yVel += self.grav/2

        if pressedKeys[0]:
            if self.controls[0][1] == False:
                self.controls[0][1] = True
                if self.jumps[1] > 0:
                    if self.coyoteTime > 0 or self.jumps[0]-1 == self.jumps[1]:
                        self.jumps[1] -= 1
                        self.jump()
                    else:
                        if (self.jumps[1] == self.jumps[0]) and self.yVel > 0.5:
                            self.jumps[1] = 0
                            self.jump()
        else:
            self.controls[0][1] = False
        self.changePos(0, self.yVel)

        nearbyTiles = self.getNearbyTiles()
        for tile in nearbyTiles:
            tile.collide(self, 'y')

        if self.coyoteTime > 0:
            self.coyoteTime -= 1

    def cameraMove(self):
        global currentMap
        rightCameraBorder = self.rect[0]+self.size > WIDTH*0.6-self.cameraPos[0] and self.xVel > 0.75 and self.cameraPos[0] > -(len(currentMap.map[0]))*TILESIZE+WIDTH
        leftCameraBorder = self.rect[0] < WIDTH*0.4-self.cameraPos[0] and self.xVel < -0.75 and self.cameraPos[0] < 0
        topCameraBorder = self.rect[1] < HEIGHT*0.4-self.cameraPos[1] and self.yVel < -0.75 and self.cameraPos[1] < 0
        bottomCameraBorder = self.rect[1]+self.size > HEIGHT*0.4-self.cameraPos[1] and self.yVel > 0.75 and self.cameraPos[1] > -(len(currentMap.map))*TILESIZE+HEIGHT

        if leftCameraBorder or rightCameraBorder:
            self.cameraPos = (self.cameraPos[0]-self.xVel, self.cameraPos[1])
            self.offsetX += self.xVel

        if topCameraBorder or bottomCameraBorder:
            self.cameraPos = (self.cameraPos[0], self.cameraPos[1]-self.yVel)
            self.offsetY += self.yVel

        if self.cameraPos[0] > 0:
            self.offsetX += self.cameraPos[0]
            self.cameraPos = (0, self.cameraPos[1])
        if self.cameraPos[0] < -(len(currentMap.map[0]))*TILESIZE+WIDTH:
            self.offsetX += self.cameraPos[0]-(-(len(currentMap.map[0]))*TILESIZE+WIDTH)
            self.cameraPos = (-(len(currentMap.map[0]))*TILESIZE+WIDTH, self.cameraPos[1])

        if self.cameraPos[1] > 0:
            self.offsetY += self.cameraPos[1]
            self.cameraPos = (self.cameraPos[0], 0)
        if self.cameraPos[1] < -(len(currentMap.map))*TILESIZE+HEIGHT:
            self.offsetY += self.cameraPos[1]-(-(len(currentMap.map))*TILESIZE+HEIGHT)
            self.cameraPos = (self.cameraPos[0], -(len(currentMap.map))*TILESIZE+HEIGHT)

    def getNearbyTiles(self):
        global currentMap
        nearbyTiles = []
        xMin, xMax, yMin, yMax =  math.floor(self.rect[0]/TILESIZE-1), math.ceil(self.rect[0]/TILESIZE+2), math.floor(self.rect[1]/TILESIZE-1), math.ceil(self.rect[1]/TILESIZE+2)

        for row in range(yMin, yMax):
            for tile in range(xMin, xMax):
                try:
                    if currentMap.tiles[row][tile] != None:
                        nearbyTiles.append(currentMap.tiles[row][tile])
                except IndexError:
                    pass

        return nearbyTiles

    def remove(self):
        global playerList
        playerList.remove(self)

    def update(self):
        global playerList
        self.cameraMove()
        if self.deathTimer == 0 and not self.won:
            self.move()
        if self.rect[1] > (len(currentMap.map)+2)*TILESIZE:
            self.die('fell')
        self.camera.fill((255, 255, 255))
        currentMap.update(self)
        self.debug_drawRect()

        self.fade()

        self.camera.blit(self.fadeLayer)

def drawCamera():
    global playerList
    players = len(playerList)
    if players == 1:
        screen.blit(playerList[0].camera)
    elif players == 2:
        for player in range(len(playerList)):
            screen.blit(pygame.transform.scale_by(playerList[player].camera, 0.5), dest=(WIDTH/4, HEIGHT/2*player))
    elif players == 3:
        for player in range(len(playerList)):
            screen.blit(pygame.transform.scale_by(playerList[player].camera, 0.5), dest=(WIDTH/4*player, HEIGHT/2*(player%2)))
    elif players == 4:
        for player in range(len(playerList)):
            screen.blit(pygame.transform.scale_by(playerList[player].camera, 0.5), dest=(WIDTH/2*(player%2), HEIGHT/2*math.floor(player/2)))


def checkKeypress(keyList):
    keys = pygame.key.get_pressed()
    requestedKeys = []
    for key in keyList:
        requestedKeys.append(keys[key[0]])
    return requestedKeys

def update():
    global playerList
    clock.tick(FPS)

    screen.fill((255, 255, 255))

    for player in playerList:
        player.update()
    
    drawCamera()

    pygame.display.flip()

currentMap = Map('assets/lv1')

playerList = []
#controls: up, left, down, right
P1 = Player([pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d])
P2 = Player([pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT])
P3 = Player([pygame.K_t, pygame.K_f, pygame.K_g, pygame.K_h])
P4 = Player([pygame.K_i, pygame.K_j, pygame.K_k, pygame.K_l])

def setPlayerList():
    global playerList
    playerList = []
    if PLAYERS >= 1:
        playerList.append(P1)
    if PLAYERS >= 2:
        playerList.append(P2)
    if PLAYERS >= 3:
        playerList.append(P3)
    if PLAYERS >= 4:
        playerList.append(P4)

setPlayerList()

run = True

while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    update()