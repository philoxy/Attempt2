import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame, xml.etree.ElementTree as ET, math
pygame.mixer.init()
pygame.font.init()
WIDTH = 640
HEIGHT = 480
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED|pygame.RESIZABLE, vsync=1)
#icon = pygame.image.load("assets/icon.png").convert_alpha()
pygame.display.set_caption("Attempt 2")
#pygame.display.set_icon(icon)
clock = pygame.time.Clock()

#todo
#camera movement
#collision (doom)

def loadimg(img):
    return pygame.image.load(img).convert_alpha()

class Tile():
    def __init__(self, x, y):
        self.rect = pygame.Rect(x*40, y*40, 40, 40)
    
    def xCollide(self, object):
        colliding = self.rect.colliderect(object.rect)
        if object.xVel < 0:
            changeX = 0.5
        elif object.xVel > 0:
            changeX = -0.5

        while colliding:
            object.changePos(changeX, 0)
            object.xVel = 0
            colliding = self.rect.colliderect(object.rect)

    def yCollide(self, object):
        colliding = self.rect.colliderect(object.rect)
        if object.yVel < 0:
            changeY = 1
        elif object.yVel > 0:
            changeY = -1
        while colliding:
            if changeY == -1:
                object.jumps[1] = object.jumps[0]
            object.changePos(0, changeY)
            object.yVel = 0
            colliding = self.rect.colliderect(object.rect)

class Map():
    def __init__(self, folder):
        self.spritesheet = loadimg(f'{folder}/tileset.png')
        self.bg = loadimg(f'{folder}/bg.png')
        self.map = []
        self.parsetmx(folder)
        self.tiles = self.map
        self.draw()

    def parsetmx(self, folder): #i put it in a function because its ugly
        tree = ET.parse(f'{folder}/map.tmx')
        root = tree.getroot()
        mapstr = root[1][0].text
        tempMap = mapstr.split("\n")
        for row in tempMap:
            self.map.append(row.split(","))
        self.map.pop(0)
        self.map.pop()
        for row in range(len(self.map)-1):
            self.map[row].pop()

    def draw(self):
        self.mapsurf = pygame.Surface(( 40*len(self.map[0]), 40*len(self.map) ), pygame.SRCALPHA) #tilesize is 40 and im not changing that
        self.mapsurf.convert_alpha()
        x, y = -1, -1
        for row in self.map:
            y += 1
            x = -1
            for tile in row:
                tile = int(tile)
                x += 1
                if tile != 0:
                    self.mapsurf.blit(self.spritesheet, dest=(x*40, y*40), area=(((tile-1)%5)*40, math.floor((tile-1)/5)*40, 40, 40))
                    self.tiles[y][x] = Tile(x, y)
                else:
                    self.tiles[y][x] = None

    def drawBG(self):
        global playerList
        for player in playerList:
            player.camera.blit(self.bg, dest=((player.cameraPos[0]/4)%640-640, player.cameraPos[1]))
            player.camera.blit(self.bg, dest=((player.cameraPos[0]/4)%640, player.cameraPos[1]))
                    
    def update(self):
        global playerList
        for player in playerList:
            player.camera.blit(self.mapsurf, dest=player.cameraPos)

currentMap = Map('assets/lv1')

playerList = []

class Player():
    def __init__(self, controls):
        global playerList
        self.rect = pygame.Rect(0, 0, 40, 40)
        self.offsetX = 0
        self.offsetY = 0
        self.cameraPos = (0, 0)
        self.camera = pygame.Surface((WIDTH, HEIGHT))
        self.controls = []
        for button in controls:
            self.controls.append([button, False])
        self.xVel = 0
        self.yVel = 0
        self.grav = 1
        self.speed = 5
        self.facing = 1 #0 = left 1 = right
        playerList.append(self)
        self.jumps = [2, 2]

    def setPos(self, x, y):
        self.rect = (x, y, 40, 40)

    def changePos(self, x, y):
        self.rect = (self.rect[0] + x, self.rect[1] + y, 40, 40)

    def debug_drawRect(self):
        tempRect = (int(self.rect[0]-self.offsetX), int(self.rect[1]-self.offsetY), 40, 40)
        pygame.draw.rect(self.camera, (255, 0, 0), tempRect)

    def move(self):
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
            tile.xCollide(self)

        self.yVel += self.grav/2

        if pressedKeys[0]:
            if self.controls[0][1] == False:
                self.controls[0][1] = True
                if self.jumps[1] != 0:
                    self.yVel = -self.grav*10
                    self.jumps[1] -= 1
        else:
            self.controls[0][1] = False
        self.changePos(0, self.yVel)

        nearbyTiles = self.getNearbyTiles()
        for tile in nearbyTiles:
            tile.yCollide(self)

    def cameraMove(self):
        global currentMap
        leftCameraBorder = self.rect[0]+40 > WIDTH*(0.6)-self.cameraPos[0] and self.xVel > 0.75 and self.cameraPos[0] > -(len(currentMap.map[0]))*40+640
        rightCameraBorder = self.rect[0] < WIDTH*(0.4)-self.cameraPos[0] and self.xVel < -0.75 and self.cameraPos[0] < 0
        if self.cameraPos[0] > 0:
            self.cameraPos = (0, self.cameraPos[1])
        if self.cameraPos[0] < -(len(currentMap.map[0]))*40+640:
            self.cameraPos = (-(len(currentMap.map[0]))*40+640, self.cameraPos[1])
        if leftCameraBorder or rightCameraBorder:
            self.cameraPos = (self.cameraPos[0]-self.xVel, self.cameraPos[1])
            if abs(self.xVel) < 0.75:
                self.xVel = 0
            self.offsetX += self.xVel

    def getNearbyTiles(self):
        global currentMap
        nearbyTiles = []
        xMin, xMax, yMin, yMax =  math.floor((self.rect[0])/40-1), math.ceil((self.rect[0])/40+2), math.floor((self.rect[1])/40-1), math.ceil((self.rect[1])/40+2)

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
        self.cameraMove()
        self.move()
        self.camera.fill((255, 255, 255))
        currentMap.drawBG()
        currentMap.update()
        self.debug_drawRect()

        screen.blit(self.camera)

P1 = Player([pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d])

def checkKeypress(keyList):
    keys = pygame.key.get_pressed()
    requestedKeys = []
    for key in keyList:
        requestedKeys.append(keys[key[0]])
    return requestedKeys

def update():
    global playerList
    clock.tick(60)

    screen.fill((255, 255, 255))

    for player in playerList:
        player.update()

    pygame.display.flip()

run = True

while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    update()