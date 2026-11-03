# by Philooxy | https://philoxy.github.io/

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame, xml.etree.ElementTree as ET, math, sys, time, json
pygame.mixer.init()
pygame.font.init()
WIDTH = 640
HEIGHT = 480
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED|pygame.RESIZABLE, vsync=1)
icon = pygame.image.load("assets/icon.png").convert_alpha()
pygame.display.set_caption("Attempt 2")
pygame.display.set_icon(icon)
clock = pygame.time.Clock()

font_s = pygame.font.Font('assets/95.otf')
font = pygame.font.Font('assets/95.otf', size=24)
font_m = pygame.font.Font('assets/95.otf', size=32)
font_l = pygame.font.Font('assets/95.otf', size=36)

TILESIZE = 40
FPS = 60
FADE_O = 255 #opaque
FADE_T = 0 #transparent
PLAYERS = 1
MINUTE = 3600
SHOWHITBOXES = 0
PLAYERCOLLISION = 1

def loadimg(img):
    return pygame.image.load(img).convert_alpha()

img_obj = loadimg('assets/objects.png')
img_flag = loadimg('assets/flags.png')
img_rock = loadimg('assets/tilesets/rock.png')
#img_grass = loadimg('assets/tilesets/blugrass.png')

snd_spring = pygame.mixer.Sound('assets/sfx/spring.mp3')
snd_die = pygame.mixer.Sound('assets/sfx/death.mp3')
snd_fall = pygame.mixer.Sound('assets/sfx/fall.mp3')
snd_win = pygame.mixer.Sound('assets/sfx/tada.mp3')

def ease(t):
    return 1 - ((1 - t) ** 3)

def collide(object, rect, direction):
    doCollide = True
    if isinstance(object, Player):
        if object.deathType != '':
            doCollide = False
    if doCollide:
        if direction == 'x':
            colliding = rect.colliderect(object.rect)
            if object.xVel < 0:
                changeX = 0.1
            elif object.xVel > 0:
                changeX = -0.1

            while colliding:
                object.changePos(changeX, 0)
                object.xVel = 0
                colliding = not(pygame.Rect(object.rect).left == rect.right or pygame.Rect(object.rect).right == rect.left)

        elif direction == 'y':
            colliding = rect.colliderect(object.rect)
            if object.yVel < 0:
                changeY = 0.1
            elif object.yVel > 0:
                changeY = -0.1
            while colliding:
                if isinstance(object, Player):
                    if changeY == -0.1:
                        object.jumps[1] = object.jumps[0]
                        object.coyoteTime = 8
                object.changePos(0, changeY)
                object.yVel = 0
                colliding = not(pygame.Rect(object.rect).top == rect.bottom or pygame.Rect(object.rect).bottom == rect.top)

#objects
class Spring:
    def __init__(self, x, y, rotation):
        self.pos = (x, y)
        self.activateTimer = 0
        self.boingness = 15
        rotation = round(rotation/90)
        self.rotation = rotation
        match rotation:
            case 0:
                x, y, w, h = 0, TILESIZE-25, TILESIZE, 25
            case 1:
                x, y, w, h = 0, 0, 25, TILESIZE
                self.pos = (self.pos[0], self.pos[1]+TILESIZE)
            case 2:
                x, y, w, h = 0, 0, TILESIZE, 25
                self.pos = (self.pos[0]-TILESIZE, self.pos[1]+TILESIZE)
            case 3:
                x, y, w, h = TILESIZE-25, 0, 25, TILESIZE
                self.pos = (self.pos[0]-TILESIZE, self.pos[1])
        self.rect = pygame.Rect(self.pos[0]+x, self.pos[1]+y, w, h)

        self.image_unboing = pygame.Surface((TILESIZE, TILESIZE), pygame.SRCALPHA)
        self.image_unboing.blit(img_obj, area=(0, 0, TILESIZE, TILESIZE))
        self.image_unboing = pygame.transform.rotate(self.image_unboing, -rotation*90)

        self.image_boing = pygame.Surface((TILESIZE, TILESIZE), pygame.SRCALPHA)
        self.image_boing.blit(img_obj, area=(TILESIZE, 0, TILESIZE, TILESIZE))
        self.image_boing = pygame.transform.rotate(self.image_boing, -rotation*90)

    def collide(self, object):
        if self.rect.colliderect(object.rect):
            match self.rotation:
                case 0:
                    object.yVel = -self.boingness
                case 1:
                    object.xVel = self.boingness
                case 2:
                    object.yVel = self.boingness
                case 3:
                    object.xVel = -self.boingness
            if isinstance(object, Player):
                object.jumps[1] = 1
            self.activateTimer = 30


    def update(self, player=None):
        global playerList

        if self.activateTimer > 0:
            self.activateTimer -= 1
            self.image = self.image_boing
        else:
            self.image = self.image_unboing

        if self.activateTimer == 28:
            snd_spring.play()

        if player != None:
            player.camera.blit(self.image, dest=(player.cameraPos[0]+self.pos[0], player.cameraPos[1]+self.pos[1]))
            self.collide(player)
        
class Goal:
    def __init__(self, x, y, type):
        self.type = type
        self.pos = (x, y-TILESIZE/2)
        self.rect = pygame.Rect(self.pos[0], self.pos[1], TILESIZE, TILESIZE*1.5)
        if type == 'normal':
            self.sprite = (0, 0, TILESIZE, TILESIZE*1.5)
        elif type == 'secret':
            self.sprite = (TILESIZE, 0, TILESIZE, TILESIZE*1.5)
        self.frame = 0
        self.anim = 0

    def collide(self, player):
        if self.rect.colliderect(player.rect) and player.deathType == '':
            player.win(self.type)

    def update(self, player):
        player.camera.blit(img_flag, dest=(player.cameraPos[0]+self.pos[0], player.cameraPos[1]+self.pos[1]+1), area=(self.sprite[0], self.frame*(TILESIZE*1.5), self.sprite[2], self.sprite[3]))
        self.collide(player)
        self.anim += 1
        if self.anim > 59:
            self.anim = 0
        self.frame = math.floor(self.anim/20)

class Spike:
    def __init__(self, x, y, rotation):
        self.pos = (x, y)
        self.sprite = (80, 0, 40, 40)
        rotation = round(rotation/90)
        match rotation:
            case 0:
                x, y, w, h = 16, 10, 8, 20 #less random values
            case 1:
                x, y, w, h = 10+8, 16, 20, 8
                self.pos = (self.pos[0], self.pos[1]+TILESIZE)
            case 2:
                x, y, w, h = 16, 10, 8, 20
                self.pos = (self.pos[0]-TILESIZE, self.pos[1]+TILESIZE)
            case 3:
                x, y, w, h = 10+8, 16, 20, 8
                self.pos = (self.pos[0]-TILESIZE, self.pos[1])
        self.rect = pygame.Rect(self.pos[0]+x, self.pos[1]+y, w, h)
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.image.blit(img_obj, area=self.sprite)
        self.image = pygame.transform.rotate(self.image, -rotation*90)

    def collide(self, object):
        if self.rect.colliderect(object.rect):
            if isinstance(object, Player):
                if object.deathType == '':
                    object.deathType = 'spike'

    def update(self, player):
        player.camera.blit(self.image, dest=(int(player.cameraPos[0])+self.pos[0], int(player.cameraPos[1])+self.pos[1]))
        if SHOWHITBOXES == 1:
            pygame.draw.rect(player.camera, (255, 255, 0), (int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1], self.rect[2], self.rect[3]))

        self.collide(player)

class Text:
    def __init__(self, x, y, text, fontsize):
        tempFont = pygame.font.Font('assets/95.otf', int(fontsize))
        self.text, self.text_rect = drawText(text, tempFont)
        self.text_rect.topleft = (float(x), float(y)+TILESIZE)

    def update(self, player):
        global playerList
        if len(playerList) == 1:
            player.camera.blit(self.text, dest=(int(player.cameraPos[0]+self.text_rect[0]), int(player.cameraPos[1]+self.text_rect[1]) ))

class Checkpoint:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILESIZE, TILESIZE)
        self.sprite = (120, 0, 40, 40)
        self.pointChecked = False

    def update(self, player):
        if self.rect.colliderect(player.rect) and not self.pointChecked and player.deathType == '':
            self.pointChecked = True
            player.lastCheckpoint = (self.rect[0], self.rect[1])
        if self.pointChecked:
            self.sprite = (160, 0, 40, 40)
        player.camera.blit(img_obj, dest=(int(player.cameraPos[0]+self.rect[0]), int(player.cameraPos[1]+self.rect[1]+math.sin(player.timer/20)*4-4)), area=self.sprite)
        if SHOWHITBOXES == 1:
            pygame.draw.rect(player.camera, (0, 255, 0), (int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1], self.rect[2], self.rect[3]))

class Door:
    def __init__(self, x, y, id):
        self.rect = pygame.Rect(x, y, TILESIZE, TILESIZE)
        self.unlocked = False
        self.id = int(id)

    def update(self, player):
        if self.unlocked:
            self.sprite = (0, 0, 0, 0)
        else:
            self.sprite = (TILESIZE*2, TILESIZE, TILESIZE, TILESIZE)
        player.camera.blit(img_obj, dest=(int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1]), area=self.sprite)

class Button:
    def __init__(self, x, y, rotation, doorIDs):
        y += TILESIZE
        self.pos = (x, y)
        self.imagePos = (x, y)
        self.rotation = round(rotation/90)
        self.connectedDoorIDs = doorIDs
        self.pressed = False
        self.pressing = False
        match self.rotation:
            case 0:
                x, y, w, h = 0, TILESIZE-5, TILESIZE, 5
                x2, y2, w2, h2 = 6, TILESIZE-13, 28, 8
                #x3, y3, w3, h3
                self.imagePos = (self.pos[0], self.pos[1]-5)
                self.pos = (self.pos[0], self.pos[1]-TILESIZE)
            case 1:
                x, y, w, h = 0, 0, 5, TILESIZE
                x2, y2, w2, h2 = 5, 6, 8, 28
                self.imagePos = (self.pos[0], self.pos[1]+TILESIZE-5)
            case 2:
                x, y, w, h = 0, 0, TILESIZE, 5
                x2, y2, w2, h2 = 6, 5, 28, 8
                self.imagePos = (self.pos[0]-TILESIZE, self.pos[1]+TILESIZE-5)
                self.pos = (self.pos[0]-TILESIZE, self.pos[1])
            case 3:
                x, y, w, h = TILESIZE-5, 0, 5, TILESIZE
                x2, y2, w2, h2 = TILESIZE-13, 6, 8, 28
                self.imagePos = (self.pos[0]-TILESIZE, self.pos[1]-5)
                self.pos = (self.pos[0]-TILESIZE, self.pos[1]-TILESIZE)

        self.rect = pygame.Rect(self.pos[0]+x, self.pos[1]+y, w, h)
        self.buttonrect = pygame.Rect(self.pos[0]+x2, self.pos[1]+y2, w2, h2)
        self.image = pygame.Surface((TILESIZE, TILESIZE), pygame.SRCALPHA)
        self.rect_button = self.buttonrect

    def update(self, player):
        global currentMap
        if not self.pressed:
            self.sprite = (0, TILESIZE, TILESIZE, TILESIZE)
            self.rect_button = self.buttonrect
        else:
            self.sprite = (TILESIZE, TILESIZE, TILESIZE, TILESIZE)
        self.image.fill((0,0,0,0))
        self.image.blit(img_obj, area=self.sprite)
        self.image = pygame.transform.rotate(self.image, -self.rotation*90)
        if pygame.Rect(player.rect).colliderect(self.rect_button) and not self.pressed:
            self.pressed = True
            for door in currentMap.doors:
                if door.id in self.connectedDoorIDs:
                    door.unlocked = True

        player.camera.blit(self.image, dest=(int(player.cameraPos[0])+self.imagePos[0], int(player.cameraPos[1])+self.imagePos[1]-TILESIZE+5))
        if SHOWHITBOXES == 1:
            pygame.draw.rect(player.camera, (0, 0, 255), (int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1], self.rect[2], self.rect[3]))
            pygame.draw.rect(player.camera, (0, 255, 255), (int(player.cameraPos[0])+self.buttonrect[0], int(player.cameraPos[1])+self.buttonrect[1], self.buttonrect[2], self.buttonrect[3]))

#not objects
class Tile:
    def __init__(self, x, y, collide):
        self.rect = pygame.Rect(x*TILESIZE, y*TILESIZE, TILESIZE, TILESIZE)
        self.bg = not collide


class Map:
    def __init__(self, folder):
        self.path = folder
        self.bg = loadimg(f'{folder}/bg.png')
        self.mus = pygame.mixer.Sound(f'{folder}/mus.mp3')
        with open(f'{folder}/mus.pxy', 'r') as file:
            mus_md = file.readlines()
            mus_info = f'{mus_md[0]} - {mus_md[1]}'
            mus_info = ''.join(mus_info.splitlines())
        mus_info, mus_info_rect = drawText(f'{mus_info}', font=font_s)
        note = loadimg('assets/note.png')
        self.musPopup = pygame.Surface((22+mus_info_rect[2]+2,mus_info_rect[3]), pygame.SRCALPHA)
        self.musPopup.fill((0,0,0,50))
        self.musPopup.blit(note, dest=(1, 1))
        self.musPopup.blit(mus_info, dest=(22, 1))
        self.musPopupTimer = 0
        self.musPopupPos = 0
        self.map, self.bgmap = [], []
        self.parsetmx(folder)
        self.loadObjects()
        self.map, self.tiles, self.mapsurf = self.draw(self.map)
        self.bgmap, a, self.bgmapsurf = self.draw(self.bgmap, False)
        self.bgmapsurf.fill((128,128,128), special_flags=pygame.BLEND_RGB_MULT)

        self.mus.play(loops=-1)

    def loadObjects(self):
        tempObjects = self.objects
        self.objects, self.doors, self.buttons = [], [], []
        exit, secretexit = False, False
        for object in tempObjects:
            try:
                x, y, type = float(object.attrib['x']), float(object.attrib['y'])-TILESIZE, object.attrib['type']
            except:
                print("Error: Failed to load object: No specified type!")
                print(f'Object ID: {object.attrib['id']}')
                print("Set the 'Class' value of this object to a valid object type!")
                print("")
            match type:
                case 'Spring':
                    try:
                        rotation = int(float(object.attrib['rotation']))
                    except KeyError:
                        rotation = 0
                    self.objects.append(Spring(x, y, rotation))
                case 'Exit':
                    if not exit:
                        self.objects.append(Goal(x, y, 'normal'))
                        exit == True
                case 'Secret Exit':
                    if not secretexit:
                        self.objects.append(Goal(x, y, 'secret'))
                        secretexit == True
                case 'Spike':
                    try:
                        rotation = int(float(object.attrib['rotation']))
                    except KeyError:
                        rotation = 0
                    self.objects.append(Spike(x, y, rotation))
                case 'Text':
                    text = object.find("text")
                    if text.text == None:
                        print("Error: Failed to load text object: No text specified")
                        print(f'Object ID: {object.attrib['id']}')
                        print("Please specify a text value!")
                        print("Ignoring object...")
                        print("")
                    else:
                        try:
                            textSize = int(float(text.attrib["pixelsize"]))
                        except KeyError:
                            textSize = 16
                        self.objects.append(Text(x, y, text.text, textSize))
                case 'Checkpoint':
                    self.objects.append(Checkpoint(x, y))
                case 'Button':
                    findPropertyFail = True
                    try:
                        rotation = int(float(object.attrib['rotation']))
                    except KeyError:
                        rotation = 0
                    try:
                        if object.find("properties").find("property").attrib["name"] == 'Doors':
                            findPropertyFail = False
                    except TypeError, AttributeError:
                        pass
                    if findPropertyFail:
                        print("Error: Failed to load button door list: No 'Doors' property")
                        print(f'Object ID: {object.attrib['id']}')
                        print("Give the button a custom property called 'Doors',")
                        print("make it a list, and add all the doors that you")
                        print("want to open with this button.")
                        print("")
                    else:
                        doorIDs = []
                        for door in object.find("properties").find("property"):
                            doorIDs.append(int(door.attrib["value"]))
                        tempButton = Button(x, y, rotation, doorIDs)
                        #self.objects.append(tempButton)
                        self.buttons.append(tempButton)
                case 'Door':
                    tempDoor = Door(x, y, object.attrib["id"])
                    self.objects.append(tempDoor)
                    self.doors.append(tempDoor)
                case 'Spawn':
                    pass
                case _:
                    print("Error: Failed to load object: Unknown object type")
                    print(f'Object ID: {object.attrib['id']}')
                    print(f'Object Class: {object.attrib['type']}')
                    print("Set the 'Class' value of this object to a valid object type!")
                    print("")


    def parsetmx(self, folder):
        tree = ET.parse(f'{folder}/map.tmx')
        root = tree.getroot()
        for item in root:
            if item.tag == "layer":
                if item.attrib["name"] == "Tiles":
                    mapstr = item.find("data").text
                if item.attrib["name"] == "Background":
                    bgmapstr = item.find("data").text
            if item.tag == "objectgroup" and item.attrib["name"] == "Objects":
                self.objects = item
        foundSpawn = False
        for object in self.objects:
            try:
                if object.attrib['type'] == 'Spawn':
                    self.spawnPos = (int(object.attrib['x']), int(object.attrib['y']))
                    foundSpawn = True
                    break
            except KeyError:
                pass
        if not foundSpawn:
            print("Error: No spawn point found!")
            print("Please add a spawn object to the object layer of this level,")
            print("and set the 'Class' variable to 'Spawn'.")
            print("Setting spawn to default (0,0)...")
            print("")
            self.spawnPos = (0, 0)

        tempMap = mapstr.split("\n")
        for row in tempMap:
            self.map.append(row.split(","))
        self.map.pop(0)
        self.map.pop()
        for row in range(len(self.map)-1):
            self.map[row].pop()

        tempBGMap = bgmapstr.split("\n")
        for row in tempBGMap:
            self.bgmap.append(row.split(","))
        self.bgmap.pop(0)
        self.bgmap.pop()
        for row in range(len(self.bgmap)-1):
            self.bgmap[row].pop()

    def draw(self, map, collision=True):
        mapsurf = pygame.Surface(( TILESIZE*len(map[0]), TILESIZE*len(map) ), pygame.SRCALPHA)
        mapsurf.convert_alpha()
        tiles = map
        x, y = -1, -1
        for row in map:
            y += 1
            x = -1
            for tile in row:
                tile = int(tile)
                x += 1
                if 0 < tile <= 25:
                    mapsurf.blit(img_rock, dest=(x*TILESIZE, y*TILESIZE), area=(((tile-1)%5)*TILESIZE, math.floor((tile-1)/5)*TILESIZE, TILESIZE, TILESIZE))
                    tiles[y][x] = Tile(x, y, collide=collision)
                else:
                    tiles[y][x] = None

        return map, tiles, mapsurf

    def drawBG(self, player):
        player.camera.blit(self.bg, dest=((player.cameraPos[0]/4)%640-640, 0))
        player.camera.blit(self.bg, dest=((player.cameraPos[0]/4)%640, 0))
                    
    def update(self, player):
        self.drawBG(player)
        player.camera.blit(self.bgmapsurf, dest=player.cameraPos)
        player.camera.blit(self.mapsurf, dest=player.cameraPos)
        for object in self.objects:
            object.update(player)
        if self.musPopupTimer < 210 and PLAYERS == 1:
            self.musPopupTimer += 1
            if self.musPopupTimer <= 30:
                self.musPopupPos = (self.musPopupTimer/30-1)*self.musPopup.get_width()
            elif self.musPopupTimer >= 180:
                self.musPopupPos = ((self.musPopupTimer-150)/30-1)*-self.musPopup.get_width()
            player.camera.blit(self.musPopup, (self.musPopupPos, HEIGHT-40))



class Player:
    def __init__(self, controls, char):
        self.lastCheckpoint = (currentMap.spawnPos[0], currentMap.spawnPos[1]-TILESIZE)
        self.spawnPoint = self.lastCheckpoint
        self.reset()
        self.camera = pygame.Surface((WIDTH, HEIGHT), pygame.SCALED)
        self.fadeLayer = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
        self.fadeLayer.fill((0,0,0,255))
        self.fadeLayer.set_alpha(0)
        self.controls = []
        self.keysDown = []
        for button in controls:
            self.controls.append(button)
            self.keysDown.append(False)
        self.timer = 0
        self.score = 0
        self.anim = 0
        self.frame = 0
        self.spritesheet = loadimg(f'assets/players/{char}.png')

    def reset(self):
        global currentMap
        self.size = 40
        self.playerSprite = pygame.Surface((int(self.size*3/4), self.size), pygame.SRCALPHA)
        self.jumps = [2, 1]
        self.deathTimer, self.winTimer = 0, -1
        self.offsetX = 0
        self.offsetY = 0
        self.spawnPoint = self.lastCheckpoint
        self.rect = pygame.Rect(self.lastCheckpoint[0], self.lastCheckpoint[1], int(self.size*0.6), int(self.size*0.75))
        self.cameraPos = (-self.rect[0]+(WIDTH/2-20), -self.rect[1]-TILESIZE+(HEIGHT/2-20))
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
        self.facing = 1
        self.dead = False
        self.deathType = ''

    def setPos(self, x, y):
        self.rect = (x, y, self.rect[2], self.rect[3])

    def changePos(self, x, y):
        self.rect = (round(self.rect[0] + x, 2), round(self.rect[1] + y, 2), self.rect[2], self.rect[3])

    def debug_drawRect(self):
        global playerList
        tempRect = getPlayerRect(self, (self.offsetX, self.offsetY))
        pygame.draw.rect(self.camera, (255, 0, 0), tempRect)

        for player in playerList:
            if player != self:
                tempRect = getPlayerRect(player, (self.offsetX, self.offsetY))
                pygame.draw.rect(self.camera, (255, 0, 0), tempRect)

    def win(self, exitType):
        global playerList, currentMap
        if not self.won:
            self.setFadeVars(100, 100)
            self.score = int(self.score)
            if self.timer < MINUTE/2:
                self.score += 5000
            elif self.timer < 1*MINUTE:
                self.score += 3000
            elif self.timer < 2*MINUTE:
                self.score += 1000
            elif self.timer < 3*MINUTE:
                self.score += 500
            elif self.timer < 5*MINUTE:
                self.score += 100
            self.won = exitType
            if self.won == 'secret':
                self.score += 1000
        allWon = True
        for player in playerList:
            if player.won == False:
                allWon = False
        if allWon and self.winTimer == -1:
            currentMap.mus.stop()
            snd_win.play()
            for player in playerList:
                player.winTimer = 300
        if self.winTimer != 0 and self.winTimer != -1:
            self.winTimer -= 1
        if checkKeypress([pygame.K_RETURN])[0] and allWon:
            for player in playerList:
                player.setFadeVars(100, FADE_O)
                player.winTimer = -2
        if self.winTimer == -30:
            if len(playerList) == 1:
                currentMap.mus.stop()
            for player in playerList:
                player.lastCheckpoint = currentMap.spawnPos
                player.reset()
                player.timer = 0
                player.winTimer = -1
                player.score = 0
            allWon = False
            currentMap.mus.play()

    def die(self, deathType):
        global playerList
        if len(playerList) == 1:
            currentMap.mus.stop()
        if self.deathTimer == 0:
            if deathType == 'spike':
                snd_die.stop()
                snd_die.play()
                self.yVel = -10
                self.deathTimer = FPS*2
            elif deathType == 'fell':
                snd_fall.stop()
                snd_fall.play()
                self.deathTimer = FPS
            self.deathType = deathType
        if self.deathTimer == FPS:
            self.fadeTime = 0
            self.setFadeVars(FADE_T, FADE_O)
        self.deathTimer -= 1

        if self.deathTimer == 0:
            if len(playerList) == 1:
                currentMap.mus.play()
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

    def playerCollide(self, player, axis):
        if axis == 'x':
            colliding = pygame.Rect(self.rect).colliderect(player.rect)
            if self.xVel < 0:
                changeX = 0.5
            else:
                changeX = -0.5
            if colliding:
                if self.xVel > 0 and not checkKeypress([player.controls[3]])[0]:
                    player.xVel = 2
                elif self.xVel < 0 and not checkKeypress([player.controls[1]])[0]:
                    player.xVel = -2
            while colliding:
                self.changePos(changeX, 0)
                self.xVel = 0
                colliding = pygame.Rect(self.rect).colliderect(player.rect)
        elif axis == 'y':
            colliding = pygame.Rect(self.rect).colliderect(player.rect)
            if self.yVel < 0:
                changeY = 0.5
            else:
                changeY = -0.5

            while colliding:
                self.changePos(0, changeY)
                self.coyoteTime = 5
                if self.yVel < 0:
                    tempyVel = self.yVel
                    self.yVel = player.yVel
                    player.yVel = tempyVel
                if self.yVel > 0:
                    self.jumps[1] = self.jumps[0]
                self.yVel = 0
                if abs(player.xVel) > 0.5 and not checkKeypress([self.controls[1]])[0] and not checkKeypress([self.controls[3]])[0]:
                    self.xVel = player.xVel*1.1
                colliding = pygame.Rect(self.rect).colliderect(player.rect)


    def move(self):
        global currentMap, playerList
        pressedKeys = checkKeypress(self.controls)
        if self.deathType == '':

            if pressedKeys[1]:
                self.facing = 0
                self.xVel -= self.speed/6
            elif pressedKeys[3]:
                self.facing = 1
                self.xVel += self.speed/6

            if self.rect[0] < 0:
                self.setPos(0, self.rect[1])
                self.xVel = 0

            if self.rect[0]+self.rect[2] > len(currentMap.map[0])*TILESIZE:
                self.setPos(len(currentMap.map[0])*TILESIZE-self.rect[2], self.rect[1])
                self.xVel = 0 

            if not(abs(self.yVel) > 0 and not pressedKeys[1] and not pressedKeys[3]):     
                self.xVel *= 0.9
            else:
                self.xVel *= 0.95
            
            self.anim += abs(self.xVel*1.5/6)/10
            self.frame = int(self.anim)%4

        self.xVel = round(self.xVel, 2)

        if abs(self.xVel) <= 0.05:
            self.xVel = 0
        self.changePos(self.xVel, 0)


        if self.deathType == '':
            if PLAYERCOLLISION == 1:
                for player in playerList:
                    if player != self and not player.won:
                        self.playerCollide(player, 'x')

            nearbyTiles = self.getNearbyTiles()
            for button in currentMap.buttons:
                button.update(self)
                collide(self, button.rect, 'x')
                collide(self, button.rect_button, 'x')
            for door in currentMap.doors:
                if not door.unlocked:
                    collide(self, door.rect, 'x')
            for tile in nearbyTiles:
                collide(self, tile.rect, 'x')

        self.yVel += self.grav/2

        if pressedKeys[0] and self.deathType == '':
            if self.keysDown[1] == False:
                self.keysDown[1] = True
                if self.jumps[1] > 0:
                    if self.coyoteTime > 0 or self.jumps[0]-1 == self.jumps[1]:
                        self.jumps[1] -= 1
                        self.jump()
                    else:
                        if (self.jumps[1] == self.jumps[0]) and self.yVel > 0.5:
                            self.jumps[1] = 0
                            self.jump()
        else:
            self.keysDown[1] = False
        self.changePos(0, self.yVel)

        if PLAYERCOLLISION == 1:
            for player in playerList:
                if player != self and not player.won:
                    self.playerCollide(player, 'y')

        nearbyTiles = self.getNearbyTiles()
        for button in currentMap.buttons:
            button.update(self)
            if button.rotation != 0:
                collide(self, button.rect, 'y')
                collide(self, button.rect_button, 'y')
            else:
                collide(self, button.rect_button, 'y')
                collide(self, button.rect, 'y')
        for door in currentMap.doors:
            if not door.unlocked:
                collide(self, door.rect, 'y')
        for tile in nearbyTiles:
            collide(self, tile.rect, 'y')

        if self.coyoteTime > 0:
            self.coyoteTime -= 1

    def cameraMove(self):
        global currentMap
        rightCameraBorder = self.rect[0]+int(self.size*3/4) > WIDTH*0.6-self.cameraPos[0] and self.xVel > 0.75 and self.cameraPos[0] > -(len(currentMap.map[0]))*TILESIZE+WIDTH
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
                    if currentMap.tiles[row][tile] != None and not currentMap.tiles[row][tile].bg:
                        nearbyTiles.append(currentMap.tiles[row][tile])
                except IndexError:
                    pass

        return nearbyTiles

    def remove(self):
        global playerList
        playerList.remove(self)

    def getTime(self):
        sec = math.floor(self.timer/60)%60
        min = math.floor(math.floor(self.timer/60)/60)
        ms = int(self.timer*1000/60)%1000 #fake ms
        if abs(sec) < 10:
            sec = f'0{sec}'
        if abs(min) < 10:
            min = f'0{min}'
        if abs(int(ms)) < 10:
            ms = f'0{ms}'
        if abs(int(ms)) < 100:
            ms = f'0{ms}'
        timer = f'{min}:{sec}"{ms}'
        return timer

    def drawUI(self):
        global playerList
        if not self.won:
            self.camera.blit(self.fadeLayer)
            timer, timer_rect = drawText(f'Time: {self.getTime()}')
            self.score = int(self.score)
            for exponent in range(5):
                if abs(int(self.score)) < 10^(exponent+1):
                    self.score = f'0{self.score}'

            score, score_rect = drawText(f'Score: {self.score}')

            timer_rect.topleft = (10, 10)
            score_rect.topright = (WIDTH-10, 10)

            self.camera.blit(timer, timer_rect)
            self.camera.blit(score, score_rect)
        else:
            self.camera.blit(self.fadeLayer)
            allWon = True
            winners = len(playerList)
            for player in playerList:
                if player.won == False:
                    allWon = False
                    winners -= 1
            if not allWon:
                waiting, waiting_rect = drawText(f'Waiting for players...', font=font_l)
                playersWon, playersWon_rect = drawText(f'{winners}/{len(playerList)}')

                waiting_rect.center = (WIDTH/2, HEIGHT/3)
                playersWon_rect.center = (WIDTH/2, HEIGHT/7*3)

                self.camera.blit(waiting, waiting_rect)
                self.camera.blit(playersWon, playersWon_rect)

            else:
                if self.winTimer >= 0:
                    self.camera.blit(self.fadeLayer)
                youwin, youwin_rect = drawText('You Won!', font=font_l)
                youwin_rect.center = (WIDTH/2, HEIGHT/4)
                self.camera.blit(youwin, youwin_rect)

                if self.winTimer <= 240:
                    finalTime, finalTime_rect = drawText(f'Final Time: {self.getTime()}', font_m)
                    finalTime_rect.center = (WIDTH/2, HEIGHT/7*3)
                    self.camera.blit(finalTime, finalTime_rect)

                if self.winTimer <= 180:
                    timeBonus = 0
                    tempScore = int(self.score)
                    if self.timer < MINUTE/2:
                        tempScore -= 5000
                        timeBonus = 5000
                    elif self.timer < 1*MINUTE:
                        tempScore -= 3000
                        timeBonus = 3000
                    elif self.timer < 2*MINUTE:
                        tempScore -= 1000
                        timeBonus = 1000
                    elif self.timer < 3*MINUTE:
                        tempScore -= 500
                        timeBonus = 500
                    elif self.timer < 5*MINUTE:
                        tempScore -= 100
                        timeBonus = 100
                    if self.won == 'secret':
                        tempScore -= 1000

                    for exponent in range(5):
                        if abs(int(tempScore)) < 10^(exponent+1):
                            tempScore = f'0{tempScore}'

                    score, score_rect = drawText(f'Score: {tempScore}', font_m)

                    score_rect.center = (WIDTH/2, HEIGHT/7*4)

                    self.camera.blit(score, score_rect)

                if self.winTimer <= 120:
                    if self.won == 'secret':
                        secretExit, secretExit_rect = drawText(f'+1000 Secret Exit Bonus', font_s)
                        secretExit_rect.center = (WIDTH/2, HEIGHT/14*9)
                        self.camera.blit(secretExit, secretExit_rect)
                    if timeBonus > 0:
                        timeBonus, timeBonus_rect = drawText(f'+{timeBonus} Time Bonus', font_s)
                        timeBonus_rect.center = (WIDTH/2, HEIGHT/7*5-10)
                        self.camera.blit(timeBonus, timeBonus_rect)

                if self.winTimer <= 60:
                    for exponent in range(5):
                        if abs(int(self.score)) < 10^(exponent+1):
                            self.score = f'0{self.score}'
                    finalScore, finalScore_rect = drawText(f'Final Score: {self.score}', font_l)  
                    finalScore_rect.center = (WIDTH/2, HEIGHT/14*11)
                    self.camera.blit(finalScore, finalScore_rect)              

                if self.winTimer == 0:
                    pressstart, pressstart_rect = drawText(f'Press ENTER to continue', font_s)
                    pressstart_rect.bottomright = (WIDTH-10, HEIGHT-10)
                    self.camera.blit(pressstart, pressstart_rect)
                if self.winTimer < 0:
                    self.camera.blit(self.fadeLayer)

    def drawPlayer(self):
        global playerList

        for player in playerList:

            player.playerSprite.fill((0,0,0,0))

            if abs(player.xVel) > 1:
                sprite = (player.frame*30, 0, 30, 40)
            else:
                sprite = (0, 40, 30, 40)
            if player.yVel < 0:
                sprite = (30, 40, 30, 40)
            elif player.yVel > 0:
                sprite = (60, 40, 30, 40)
            if player.deathType != '':
                sprite = (90, 40, 30, 40)

            player.playerSprite.blit(player.spritesheet, area=sprite)

            if player.facing == 0:
                player.playerSprite = pygame.transform.flip(player.playerSprite, True, False)

            tempRect = getPlayerRect(player, (self.offsetX, self.offsetY))
            tempRect = (tempRect[0]-3, tempRect[1]-10, tempRect[2], tempRect[3])
            self.camera.blit(player.playerSprite, dest=tempRect)

    def update(self):
        global playerList
        if not self.won:
            self.move()
            if self.deathType == '':
                self.cameraMove()
        if self.deathType != '':
            self.die(self.deathType)
        if self.rect[1] > (len(currentMap.map)+2)*TILESIZE and self.deathType == '':
            self.deathType = 'fell'
        self.camera.fill((255, 255, 255))
        currentMap.update(self)
        for button in currentMap.buttons:
            button.update(self)
        if SHOWHITBOXES == 1:
            self.debug_drawRect()
        self.drawPlayer()

        if not self.won and self.deathType == '':
            self.timer += 1

        self.fade()

        self.drawUI()


def getPlayerRect(player, offsets):
    return (round(player.rect[0]-offsets[0]-player.spawnPoint[0]+(WIDTH/2-20), 2), round(player.rect[1]-offsets[1]-player.spawnPoint[1]-TILESIZE+(HEIGHT/2-20), 2), player.rect[2], player.rect[3])

def drawText(textStr, font=font):
    text = font.render(textStr, False, (255, 255, 255))
    text_rect = text.get_rect()
    return text, text_rect

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
        requestedKeys.append(keys[key])
    return requestedKeys

def update():
    global playerList, screen
    clock.tick(FPS)

    screen.fill((255, 255, 255))

    for player in playerList:
        player.update()
    
    drawCamera()

    pygame.display.flip()

currentMap = Map('assets/levels/lv1')

playerList = []
#controls: up, left, down, right
P1 = Player([pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d], 'soday')
P2 = Player([pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT], 'donnie')
P3 = Player([pygame.K_t, pygame.K_f, pygame.K_g, pygame.K_h], 'soday')
P4 = Player([pygame.K_i, pygame.K_j, pygame.K_k, pygame.K_l], 'soday')

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