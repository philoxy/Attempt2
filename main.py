import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame, xml.etree.ElementTree as ET, math, sys, time, json
pygame.mixer.init()
pygame.font.init()
WIDTH = 640
HEIGHT = 480
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED|pygame.RESIZABLE, vsync=1)
icon = pygame.image.load("assets/global/icon.png").convert_alpha()
pygame.display.set_caption("Attempt 2")
pygame.display.set_icon(icon)
clock = pygame.time.Clock()

font_s = pygame.font.Font('assets/global/95.otf')
font = pygame.font.Font('assets/global/95.otf', size=24)
font_m = pygame.font.Font('assets/global/95.otf', size=32)
font_l = pygame.font.Font('assets/global/95.otf', size=36)

TILESIZE = 40
FPS = 60
FADE_O = 255 #opaque
FADE_T = 0 #transparent
PLAYERS = 1
MINUTE = 3600
SHOWPLAYERRECT = 0

def loadimg(img):
    return pygame.image.load(img).convert_alpha()

img_obj = loadimg('assets/global/objects.png')
img_flag = loadimg('assets/global/flags.png')

snd_spring = pygame.mixer.Sound('assets/global/sfx/spring.mp3')
snd_die = pygame.mixer.Sound('assets/global/sfx/death.mp3')
snd_fall = pygame.mixer.Sound('assets/global/sfx/fall.mp3')
snd_win = pygame.mixer.Sound('assets/global/sfx/tada.mp3')

def ease(t):
    return 1 - ((1 - t) ** 3)

#objects
class Spring:
    def __init__(self, x, y):
        self.pos = (int(float(x)), int(float(y)))
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

        player.camera.blit(self.spritesheet, dest=(player.cameraPos[0]+self.pos[0]+2, player.cameraPos[1]+self.pos[1]+1), area=self.sprite)
        self.collide(player)
        
class Goal:
    def __init__(self, x, y, type):
        self.type = type
        self.pos = (int(float(x)), int(float(y))-TILESIZE/2)
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
    def __init__(self, x, y, collide):
        self.rect = pygame.Rect(x*TILESIZE, y*TILESIZE, TILESIZE, TILESIZE)
        self.bg = not collide
    
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
                changeY = 0.5
            elif object.yVel > 0:
                changeY = -0.5
            while colliding:
                if changeY == -0.5:
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
        with open(f'{folder}/mus.pxy', 'r') as file:
            mus_md = file.read()
            self.mus_title = mus_md[0]
            self.mus_artist = mus_md[1]
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
                if 0 < tile <= 25:
                    self.mapsurf.blit(self.spritesheet, dest=(x*TILESIZE, y*TILESIZE), area=(((tile-1)%5)*TILESIZE, math.floor((tile-1)/5)*TILESIZE, TILESIZE, TILESIZE))
                    self.tiles[y][x] = Tile(x, y, collide=True)
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
    def __init__(self, controls, char):
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
        self.spritesheet = loadimg(f'assets/global/players/{char}.png')

    def reset(self):
        global currentMap
        self.size = 40
        self.playerSprite = pygame.Surface((int(self.size*3/4), self.size), pygame.SRCALPHA)
        self.jumps = [2, 1]
        self.deathTimer, self.winTimer = 0, -1
        self.offsetX = 0
        self.offsetY = -10
        self.rect = pygame.Rect(currentMap.spawnPos[0], currentMap.spawnPos[1], int(self.size*0.6), int(self.size*0.75))
        self.cameraPos = (-self.rect[0]+(WIDTH/2-20), -self.rect[1]+10+(HEIGHT/2-20))
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

    def setPos(self, x, y):
        self.rect = pygame.Rect(x, y, int(self.size*0.6), int(self.size*0.75))

    def changePos(self, x, y):
        self.rect = (self.rect[0] + x, self.rect[1] + y, int(self.size*0.6), int(self.size*0.75))

    def debug_drawRect(self):
        global playerList
        tempRect = getPlayerRect(self, (self.offsetX, self.offsetY))
        pygame.draw.rect(self.camera, (255, 0, 0), tempRect)

        for player in playerList:
            if player != self:
                tempRect = getPlayerRect(player, (self.offsetX, self.offsetY))
                pygame.draw.rect(self.camera, (255, 0, 0), tempRect)

    def win(self, exitType):
        global playerList
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
            snd_win.play()
            currentMap.mus.stop()
            for player in playerList:
                player.winTimer = 300
        if self.winTimer != 0:
            self.winTimer -= 1
        if checkKeypress([pygame.K_RETURN])[0] and allWon:
            for player in playerList:
                player.setFadeVars(100, FADE_O)
                player.winTimer = -2
        if self.winTimer == -30:
            if len(playerList) == 1:
                currentMap.mus.stop()
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

        if not(abs(self.yVel) > 0 and not pressedKeys[1] and not pressedKeys[3]):     
            self.xVel *= 0.9
        self.anim += abs(self.xVel*1.5/6)/10
        self.frame = int(self.anim)%4

        if abs(self.xVel) < 0.05:
            self.xVel = 0
        self.changePos(self.xVel, 0)

        nearbyTiles = self.getNearbyTiles()
        for tile in nearbyTiles:
            tile.collide(self, 'x')

        if self.rect[0] < 0:
            self.rect = pygame.Rect(0, self.rect[1], self.rect[2], self.rect[3])
            self.xVel = 0

        if self.rect[0]+self.rect[2] > len(currentMap.map[0])*TILESIZE:
            self.rect = pygame.Rect((len(currentMap.map[0]))*TILESIZE-self.rect[2], self.rect[1], self.rect[2], self.rect[3])
            self.xVel = 0

        self.yVel += self.grav/2

        if pressedKeys[0]:
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

        nearbyTiles = self.getNearbyTiles()
        for tile in nearbyTiles:
            tile.collide(self, 'y')

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
                playersWon_rect.center =(WIDTH/2, HEIGHT/7*3)

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
            if player != self:
                player.playerSprite.fill((0,0,0,0)) #wow this is inefficient

                if abs(player.xVel) > 1:
                    sprite = (player.frame*30, 0, 30, 40)
                else:
                    sprite = (0, 40, 30, 40)
                if player.yVel < 0:
                    sprite = (30, 40, 30, 40)

                player.playerSprite.blit(player.spritesheet, area=sprite)

                if player.facing == 0:
                    player.playerSprite = pygame.transform.flip(player.playerSprite, True, False)

                tempRect = getPlayerRect(player, (self.offsetX, self.offsetY))
                tempRect = (tempRect[0]-3, tempRect[1]-10, tempRect[2], tempRect[3])
                self.camera.blit(player.playerSprite, dest=tempRect)
                

        self.playerSprite.fill((0,0,0,0))

        if abs(self.xVel) > 1:
            sprite = (self.frame*30, 0, 30, 40)
        else:
            sprite = (0, 40, 30, 40)
        if self.yVel < 0:
            sprite = (30, 40, 30, 40)

        self.playerSprite.blit(self.spritesheet, area=sprite)

        if self.facing == 0:
            self.playerSprite = pygame.transform.flip(self.playerSprite, True, False)

        tempRect = getPlayerRect(self, (self.offsetX, self.offsetY))
        tempRect = (tempRect[0]-3, tempRect[1]-10, tempRect[2], tempRect[3])
        self.camera.blit(self.playerSprite, dest=tempRect)

    def update(self):
        global playerList
        if self.deathTimer == 0 and not self.won:
            self.move()
            self.cameraMove()
        if self.rect[1] > (len(currentMap.map)+2)*TILESIZE:
            self.die('fell')
        self.camera.fill((255, 255, 255))
        currentMap.update(self)
        if SHOWPLAYERRECT == 1:
            self.debug_drawRect()
        self.drawPlayer()

        if not self.won:
            self.timer += 1

        self.fade()

        self.drawUI()


def getPlayerRect(player, offsets):
    return (int(player.rect[0]-offsets[0]-currentMap.spawnPos[0]+(WIDTH/2-20)), int(player.rect[1]-offsets[1]-currentMap.spawnPos[1]+(HEIGHT/2-20)), player.rect[2], player.rect[3])

def drawText(textStr, font=font):
    text = font.render(textStr, True, (255, 255, 255))
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

currentMap = Map('assets/lv1')

playerList = []
#controls: up, left, down, right
P1 = Player([pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d], 'soday')
P2 = Player([pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT], 'purplesoday')
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