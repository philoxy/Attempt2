# by Philooxy | https://philoxy.github.io/

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame, xml.etree.ElementTree as ET, math, sys, time, json
pygame.mixer.init()
pygame.font.init()
WIDTH = 640
HEIGHT = 480
CAM_WIDTH = 640
CAM_HEIGHT = 480
screen = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
display = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE, vsync=1)
icon = pygame.image.load("assets/icon.png").convert_alpha()
pygame.display.set_caption("Attempt 2")
pygame.display.set_icon(icon)
clock = pygame.time.Clock()

font_s = pygame.font.Font('assets/95.otf')
font = pygame.font.Font('assets/95.otf', size=24)
font_m = pygame.font.Font('assets/95.otf', size=32)
font_l = pygame.font.Font('assets/95.otf', size=36)

TILESIZE = 40 # do NOT change
FPS = 60
FADE_O = 255 #opaque
FADE_T = 0 #transparent
PLAYERS = 1
MINUTE = 3600
SHOWHITBOXES = 0
PLAYERCOLLISION = 0
CLEARMUS = 0
GROUNDPOUND_BOUNCE = 0
GROUNDPOUND_PREVENTCROUCH = 0
ALT_DEATHSPRITE = 0

def loadimg(img):
    return pygame.image.load(img).convert_alpha()

img_obj = loadimg('assets/objects.png')
img_flag = loadimg('assets/flags.png')
img_rock = loadimg('assets/tilesets/rock.png')
#img_grass = loadimg('assets/tilesets/grass.png')
img_coin = loadimg('assets/collectables.png')

snd_spring = pygame.mixer.Sound('assets/sfx/spring.mp3')
snd_spike = pygame.mixer.Sound('assets/sfx/death.mp3')
snd_fall = pygame.mixer.Sound('assets/sfx/fall.mp3')
snd_win = pygame.mixer.Sound('assets/sfx/tada.mp3')
snd_tally = pygame.mixer.Sound('assets/sfx/scoreadd.mp3')
snd_register = pygame.mixer.Sound('assets/sfx/scoretotal.mp3')
snd_button = pygame.mixer.Sound('assets/sfx/button.mp3')
snd_twinkle = pygame.mixer.Sound('assets/sfx/twinkle.mp3')

snd_twinkle.set_volume(0.8)
snd_spike.set_volume(0.8)
snd_register.set_volume(0.8)

if CLEARMUS:
    mus_clear = pygame.mixer.Sound('assets/mus/clear.mp3')

def ease(t):
    return 1 - ((1 - t) ** 3)

def collide(object, rect, direction):
    global currentMap
    collided = False
    doCollide = True
    if isinstance(object, Player):
        if object.deathType != '':
            doCollide = False
    if doCollide:
        if direction == 'x':
            if 0 < int(object.rect[1]+object.rect[3]-rect[1]) <= 10 and object.yVel == 0:
                direction = 'y'
                return
            colliding = rect.colliderect(object.rect)
            if (object.rect[0]-object.prevPos[0]) <= 0:
                changeX = 0.1
            elif (object.rect[0]-object.prevPos[0]) > 0:
                changeX = -0.1

            if colliding:
                object.prevPos = object.rect
                collided = True

            while colliding:
                object.rect = changePos(object.rect, changeX, 0)
                object.xVel = 0
                colliding = rect.colliderect(object.rect)

        if direction == 'y':
            colliding = rect.colliderect(object.rect)
            if (object.rect[1]-object.prevPos[1]) < 0:
                changeY = 0.1
            elif (object.rect[1]-object.prevPos[1]) >= 0:
                changeY = -0.1

            while colliding:
                if isinstance(object, Player):
                    if changeY == -0.1:
                        object.jumps[1] = object.jumps[0]
                        object.coyoteTime = 8
                if object.yVel > 0:
                    object.onGround = True
                object.rect = changePos(object.rect, 0, changeY)
                object.yVel = 0
                colliding = rect.colliderect(object.rect)
                collided = True
            if int(object.rect[1]+object.rect[3]-rect[1]) <= 10 and object.yVel == 0 and isinstance(object, Player) and collided:
                if object.cameraPos[1] <= 0 or object.cameraPos[1] >= -(len(currentMap.map))*TILESIZE+HEIGHT:
                    object.cameraPos = (object.cameraPos[0], object.cameraPos[1]-(object.rect[1]-object.prevPos[1]))
                    object.offsetY += (object.rect[1]-object.prevPos[1])
    return collided

def sideCollide(object, rect, side, offset=0):
    collided = False
    try:
        tempPrevPos = object.prevPos
    except AttributeError:
        tempPrevPos = object.rect
    if object.rect.colliderect(rect):
        match side:
            case 0: #top
                rect1PrevSide, rect1Side, rect2Side = tempPrevPos.bottom, object.rect.bottom, rect.top
            case 1: #left
                rect1PrevSide, rect1Side, rect2Side = tempPrevPos.right, object.rect.right, rect.left
            case 2: #bottom
                rect1PrevSide, rect1Side, rect2Side = tempPrevPos.top, object.rect.top, rect.bottom
            case 3: #right
                rect1PrevSide, rect1Side, rect2Side = tempPrevPos.left, object.rect.left, rect.right
        collided = (rect1PrevSide <= rect2Side+offset and rect1Side >= rect2Side+offset) or (rect1PrevSide >= rect2Side+offset and rect1Side <= rect2Side+offset)

    return collided


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
                    if isinstance(object, Player):
                        if object.currentAbility[0] == "gp":
                            object.yVel = -self.boingness*1.2
                        else:
                            object.yVel = -self.boingness
                    else:
                        object.yVel = -self.boingness
                case 1:
                    object.xVel = self.boingness
                case 2:
                    object.yVel = self.boingness
                case 3:
                    object.xVel = -self.boingness
            if isinstance(object, Player) and self.rotation == 0:
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
            player.camera.blit(self.image, dest=(int(player.cameraPos[0])+self.pos[0], int(player.cameraPos[1])+self.pos[1]))
            self.collide(player)
        if SHOWHITBOXES:
            pygame.draw.rect(player.camera, (255, 0, 0), (int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1], self.rect[2], self.rect[3]))
        
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
        if self.rect.colliderect(player.rect) and player.deathType == '' or player.won == self.type:
            player.win(self.type)

    def update(self, player):
        player.camera.blit(img_flag, dest=(int(player.cameraPos[0])+self.pos[0], int(player.cameraPos[1])+self.pos[1]), area=(self.sprite[0], self.frame*(TILESIZE*1.5), self.sprite[2], self.sprite[3]))
        self.collide(player)
        self.anim += 1
        if self.anim > 59:
            self.anim = 0
        self.frame = math.floor(self.anim/20)
        if SHOWHITBOXES:
            pygame.draw.rect(player.camera, (0, 0, 255), (int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1], self.rect[2], self.rect[3]))

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
                if object.deathType == '' and (object.deathType == '' or not object.won):
                    object.hurt(self)

    def update(self, player):
        player.camera.blit(self.image, dest=(int(player.cameraPos[0])+self.pos[0], int(player.cameraPos[1])+self.pos[1]))
        if SHOWHITBOXES:
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
            player.camera.blit(self.text, dest=(int(player.cameraPos[0])+self.text_rect[0], int(player.cameraPos[1])+self.text_rect[1] ))

class Checkpoint:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILESIZE, TILESIZE)
        self.sprite = (120, 0, 40, 40)

    def update(self, player):
        if self.rect.colliderect(player.rect) and player.checkpoint != self and (player.deathType == '' and not player.won):
            player.checkpoint = self
            player.lastCheckpoint = (self.rect[0], self.rect[1])
            player.health = player.maxHP
        if player.checkpoint == self:
            self.sprite = (160, 0, 40, 40)
        else:
            self.sprite = (120, 0, 40, 40)
        player.camera.blit(img_obj, dest=(int(player.cameraPos[0]+self.rect[0]), int(player.cameraPos[1]+self.rect[1]+math.sin(player.timer/20)*4-4)), area=self.sprite)
        if SHOWHITBOXES:
            pygame.draw.rect(player.camera, (0, 255, 0), (int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1], self.rect[2], self.rect[3]))

class Door:
    def __init__(self, x, y, id):
        self.rect = pygame.Rect(x, y, TILESIZE, TILESIZE)
        self.unlocked = False
        self.defaultUnlocked = False
        self.unlockable = False
        self.id = int(id)
        self.image = pygame.Surface((TILESIZE, TILESIZE), pygame.SRCALPHA)

    def objectCollide(self):
        global playerList, currentMap
        collided = False
        rects = []
        tempRect = pygame.FRect(self.rect[0]+1, self.rect[1]+1, self.rect[2]-2, self.rect[3]-2)
        for player in playerList:
            if player.canMove:
                rects.append(player.rect)
        for enemy in currentMap.enemies:
            if not enemy.dead:
                rects.append(enemy.rect)
        for rect in rects:
            if rect.colliderect(tempRect):
                collided = True
                break
        return collided

    def update(self, player):
        if not self.unlocked:
            self.image.fill(self.color)
            self.sprite = (TILESIZE*2, TILESIZE, TILESIZE, TILESIZE)
        else:
            self.image.fill((0,0,0,0))
            self.sprite = (TILESIZE*3, TILESIZE, TILESIZE, TILESIZE)
        self.image.blit(img_obj, area=self.sprite)
        self.image.fill(self.color, special_flags=pygame.BLEND_RGB_MULT)
        player.camera.blit(self.image, dest=(int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1]))

class Button:
    def __init__(self, x, y, rotation, doorIDs, color):
        self.color = color
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
                x3, y3, w3, h3 = x2, y2+4, w2, h2-4
                self.imagePos = (self.pos[0], self.pos[1]-5)
                self.pos = (self.pos[0], self.pos[1]-TILESIZE)
            case 1:
                x, y, w, h = 0, 0, 5, TILESIZE
                x2, y2, w2, h2 = 5, 6, 8, 28
                x3, y3, w3, h3 = x2, y2, w2-4, h2
                self.imagePos = (self.pos[0], self.pos[1]+TILESIZE-5)
            case 2:
                x, y, w, h = 0, 0, TILESIZE, 5
                x2, y2, w2, h2 = 6, 5, 28, 8
                x3, y3, w3, h3 = x2, y2, w2, h2-4
                self.imagePos = (self.pos[0]-TILESIZE, self.pos[1]+TILESIZE-5)
                self.pos = (self.pos[0]-TILESIZE, self.pos[1])
            case 3:
                x, y, w, h = TILESIZE-5, 0, 5, TILESIZE
                x2, y2, w2, h2 = TILESIZE-13, 6, 8, 28
                x3, y3, w3, h3 = x2+4, y2, w2-4, h2
                self.imagePos = (self.pos[0]-TILESIZE, self.pos[1]-5)
                self.pos = (self.pos[0]-TILESIZE, self.pos[1]-TILESIZE)

        self.image = pygame.Surface((TILESIZE, TILESIZE), pygame.SRCALPHA)

        self.rect = pygame.Rect(self.pos[0]+x, self.pos[1]+y, w, h)
        self.buttonrect = pygame.Rect(self.pos[0]+x2, self.pos[1]+y2, w2, h2)
        self.buttonrect_pressed = pygame.Rect(self.pos[0]+x3, self.pos[1]+y3, w3, h3)

        self.rect_button = self.buttonrect_pressed
        self.sprite_buttonrect = pygame.Rect(self.buttonrect[0]-self.pos[0], self.buttonrect[1]-self.pos[1], self.buttonrect[2], self.buttonrect[3])
        self.sprite_buttonrect_pressed = pygame.Rect(self.buttonrect_pressed[0]-self.pos[0], self.buttonrect_pressed[1]-self.pos[1], self.buttonrect_pressed[2], self.buttonrect_pressed[3])
        self.sprite_rect_button = self.sprite_buttonrect

        x, y, w, h = 0, 0, 0, 0

        match self.rotation:
            case 0:
                y, h = -1, 1
            case 1:
                x, w, = 0, 1
            case 2:
                y, h = 0, 1
            case 3:
                x, w, = -1, 1
        self.press_buttonrect = pygame.Rect(self.buttonrect[0]+x, self.buttonrect[1]+y, self.buttonrect[2]+w, self.buttonrect[3]+h)

        self.pressing = False

    def update(self, player):
        global currentMap, playerList
        if not self.pressed:
            self.sprite = (0, TILESIZE, TILESIZE, TILESIZE)
            #self.rect_button = self.buttonrect
            self.sprite_rect_button = self.sprite_buttonrect
        else:
            self.sprite = (TILESIZE, TILESIZE, TILESIZE, TILESIZE)
            self.rect_button = self.buttonrect_pressed
            self.sprite_rect_button = self.sprite_buttonrect_pressed

        self.image.fill((0,0,0,0))
        self.image.blit(img_obj, area=self.sprite)
        self.image.fill(self.color, special_flags=pygame.BLEND_RGB_MULT)
        self.image.blit(img_obj, area=(TILESIZE*4, TILESIZE, TILESIZE, TILESIZE))
        self.image = pygame.transform.rotate(self.image, -self.rotation*90)
        collided = False
        for p in playerList:
            if p.rect.colliderect(self.press_buttonrect):
                collided = True
                break
        for e in currentMap.enemies:
            if collided:
                break
            if e.rect.colliderect(self.press_buttonrect):
                collided = True
                break
        if collided:
            if not self.pressing:

                unlock = True
                for door in currentMap.doors:
                    if door.id in self.connectedDoorIDs:
                        if door.objectCollide():
                            unlock = False
                            break
                self.pressed = True
                if unlock:
                    self.pressing = True
                    snd_button.stop()
                    snd_button.play()


                    for door in currentMap.doors:
                        if door.id in self.connectedDoorIDs:
                            if not door.unlocked:
                                door.unlocked = True
                            else:
                                door.unlocked = False

        if not collided:
            self.pressing = False
            self.pressed = False

        player.camera.blit(self.image, dest=(int(player.cameraPos[0])+self.imagePos[0], int(player.cameraPos[1])+self.imagePos[1]-TILESIZE+5))
        if SHOWHITBOXES:
            pygame.draw.rect(player.camera, (0, 0, 255), (int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1], self.rect[2], self.rect[3]))
            pygame.draw.rect(player.camera, (0, 255, 255), (int(player.cameraPos[0])+self.buttonrect[0], int(player.cameraPos[1])+self.buttonrect[1], self.buttonrect[2], self.buttonrect[3]))
            pygame.draw.rect(player.camera, (255, 0, 255), (int(player.cameraPos[0])+self.press_buttonrect[0], int(player.cameraPos[1])+self.press_buttonrect[1], self.press_buttonrect[2], self.press_buttonrect[3]))

class Collectable:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x+5, y+5, 30, 30)
        self.got = False
        self.gotTimer = -1
        self.anim = 0
        self.frame = 0
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)

    def update(self, player):
        global playerList
        self.anim += 1
        if self.anim > 169:
            self.anim = 0
        self.frame = math.floor(self.anim/20)

        if self.gotTimer == -1:
            self.sprite = (-(self.frame%4*30), 0, 30, 30)
        elif self.gotTimer > 0:
            self.gotTimer -= 1
            self.sprite = (-130, 0, 30, 30)
            if self.gotTimer == 0:
                self.got = True

        self.image.fill((0,0,0,0))
        self.image.blit(img_coin, self.sprite)
        if 4 <= self.frame <= 7 and self.gotTimer == 0:
            self.image = pygame.transform.flip(self.image, True, False)

        if self.rect.colliderect(pygame.Rect(player.rect)) and self.gotTimer == -1 and (player.deathType == '' and not player.won):
            snd_twinkle.play()
            for p in playerList:
                p.coins += 1
            self.gotTimer = 7

        if not(self.gotTimer == 0):
            player.camera.blit(self.image, dest=(int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1]))
        if SHOWHITBOXES:
            pygame.draw.rect(player.camera, (200, 200, 255), (int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1], self.rect[2], self.rect[3]))
            
class Bridge:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILESIZE, 5)

    def collide(self, player):
        if isinstance(player, Player):
            if self.rect.colliderect(pygame.Rect(player.rect)) and not checkKeypress([player.controls[1]])[0] and not checkKeypress([player.controls[3]])[0]:
                player.crouchTimer += 1
            collision = True
            if player.crouchTimer > 30:
                collision = False
                if player.yVel == 0 or not player.crouching:
                    player.crouchTimer = 0
        else:
            collision = True
        if player.prevPos[1]+player.prevPos[3] <= self.rect[1]+1 and player.rect[1]+player.rect[3] >= self.rect[1] and collision:
            collide(player, self.rect, 'y')

    def update(self, player):
        player.camera.blit(img_obj, dest=(int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1]), area=(160, 80, 40, 40))
        if SHOWHITBOXES:
            pygame.draw.rect(player.camera, (200, 200, 255), (int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1], self.rect[2], self.rect[3]))

def enemymove_normal(enemy):
    global currentMap, playerList
    enemy.rect = changePos(enemy.rect, enemy.xVel, 0)
    collided = False

    if not enemy.dead:
        enemy.xVel = enemy.facing*enemy.speed

    enemy.rect = changePos(enemy.rect, enemy.xVel, 0)

    if not enemy.dead:

        for button in currentMap.buttons:
            if button.rotation != 0:
                collide(enemy, button.rect, 'x')
                collide(enemy, button.rect_button, 'x')
            else:
                collide(enemy, button.rect_button, 'x')
                collide(enemy, button.rect, 'x')
        for door in currentMap.doors:
            if not door.unlocked:
                collide(enemy, door.rect, 'x')
        for tile in getNearbyTiles(enemy):
            collide(enemy, tile.rect, 'x')
        for player in playerList:
            if not enemy.dead and enemy.rect.colliderect(player.rect) and not sideCollide(player, enemy.rect, 0):
                player.hurt(enemy)

        if enemy.xVel == 0:
            enemy.facing *= -1
            enemy.turned = True
            enemy.xVel = enemy.facing*enemy.speed
        else:
            enemy.turned = False

        if enemy.rect[0] < 0:
            enemy.rect = setPos(enemy.rect, 0, enemy.rect[1])
            enemy.facing = 1

        if enemy.rect[0]+enemy.rect[2] > len(currentMap.map[0])*TILESIZE:
            enemy.rect = setPos(enemy.rect, len(currentMap.map[0])*TILESIZE-enemy.rect[2], enemy.rect[1])
            enemy.facing = 0

    enemy.yVel += currentMap.grav/2

    enemy.rect = changePos(enemy.rect, 0, enemy.yVel)

    if not enemy.dead:
        for button in currentMap.buttons:
            if button.rotation != 0:
                collide(enemy, button.rect, 'y')
                collide(enemy, button.rect_button, 'y')
            else:
                collide(enemy, button.rect_button, 'y')
                collide(enemy, button.rect, 'y')
        for door in currentMap.doors:
            if not door.unlocked:
                collide(enemy, door.rect, 'y')
        for obj in currentMap.objects:
            if isinstance(obj, Bridge):
                obj.collide(enemy)
            if isinstance(obj, Spike):
                if enemy.rect.colliderect(obj.rect):
                    enemy.dead = True
                    enemy.yVel = -currentMap.grav*8
        for player in playerList:
            if sideCollide(player, enemy.rect, 0) and player.invuln != -1 and not player.deathType:
                enemy.dead = True
                enemy.yVel = -currentMap.grav*8
                player.yVel = -player.yVel*0.8
                player.jumps[1] = 1

    if not enemy.dead:
        for tile in getNearbyTiles(enemy):
            collide(enemy, tile.rect, 'y')

        enemy.anim += 1
        if enemy.anim > 119:
            enemy.anim = 0

        enemy.frame = int(enemy.anim/30)

    if enemy.dead:
        enemy.frame = 4

    enemy.image.fill((0,0,0,0))
    enemy.image.blit(enemy.spritesheet, area=(enemy.frame*40, 0, 40, 30))
    
    if enemy.facing == -1 and not enemy.turned:
        enemy.image = pygame.transform.flip(enemy.image, True, False)

class Enemy:
    def __init__(self, x, y, type):
        self.type = type
        self.spritesheet = loadimg(f'assets/enemies/{type}.png')
        self.originalPos = (x, y)
        self.reset()
        if self.type == "evilbrick":
            self.image = pygame.Surface((40, 30), pygame.SRCALPHA)

    def reset(self):
        self.anim = 0
        self.frame = 0
        self.xVel, self.yVel = 0, 0
        self.dead, self.deathTimer = 0, 0
        if self.type == "evilbrick":
            self.turned = True
            self.facing = 1
            self.speed = 0.5
            self.rect = pygame.Rect(self.originalPos[0], self.originalPos[1]-30, 40, 30)
        self.prevPos = self.rect
        
    def update(self, player):
        if not(self.rect[1] > (len(currentMap.map)+2)*TILESIZE and self.dead):
            match self.type:
                case "evilbrick":
                    enemymove_normal(self)

            player.camera.blit(self.image, dest=(int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1]))
            if SHOWHITBOXES:
                pygame.draw.rect(player.camera, (200, 200, 255), (int(player.cameraPos[0])+self.rect[0], int(player.cameraPos[1])+self.rect[1], self.rect[2], self.rect[3]))
            self.prevPos = self.rect



#not objects
class Tile:
    def __init__(self, x, y, collide):
        self.rect = pygame.Rect(x*TILESIZE, y*TILESIZE, TILESIZE, TILESIZE)
        self.bg = not collide

class Map:
    def __init__(self, folder):
        self.path = folder
        self.grav = 1
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
        self.loadEnemies()
        self.map, self.tiles, self.mapsurf = self.draw(self.map)
        self.bgmap, a, self.bgmapsurf = self.draw(self.bgmap, False)
        self.bgmapsurf.fill((128,128,128), special_flags=pygame.BLEND_RGB_MULT)

        self.mus.play(loops=-1)

    def loadObjects(self):
        tempObjects = self.objects
        self.objects, self.doors, self.buttons, self.coins = [], [], [], []
        exit, secretexit = False, False
        #regular objects
        for object in tempObjects:
            isText = False
            x, y = float(object.attrib['x']), float(object.attrib['y'])-TILESIZE
            try:
                type =  int(object.attrib['gid'])
            except KeyError:
                isText = True
                text = object.find("text")
                if text.text == None:
                    print("Error: Failed to load text object: No text specified")
                    print(f'Object ID: {object.attrib['gid']}')
                    print("Please specify a text value!")
                    print("Ignoring object...")
                    print("")
                else:
                    try:
                        textSize = int(float(text.attrib["pixelsize"]))
                    except KeyError:
                        textSize = 16
                    self.objects.append(Text(float(object.attrib['x']), float(object.attrib['y'])-TILESIZE, text.text, textSize))

            if not isText:
                match type:
                    case 26: #normal exit
                        if not exit:
                            self.objects.append(Goal(x, y, 'normal'))
                            exit == True
                    case 27: #secret exit
                        if not secretexit:
                            self.objects.append(Goal(x, y, 'secret'))
                            secretexit == True
                    case 28: #spawn
                        pass
                    case 29: #spring
                        try:
                            rotation = int(float(object.attrib['rotation']))
                        except KeyError:
                            rotation = 0
                        self.objects.append(Spring(x, y, rotation))
                    case 30: #spike
                        try:
                            rotation = int(float(object.attrib['rotation']))
                        except KeyError:
                            rotation = 0
                        self.objects.append(Spike(x, y, rotation))
                    case 31: #checkpoint
                        self.objects.append(Checkpoint(x, y))
                    case 32: #button
                        try:
                            rotation = int(float(object.attrib['rotation']))
                        except KeyError:
                            rotation = 0
                        doored, colored = False, False
                        fail = False
                        try:
                            for property in object.find("properties"):
                                if property.attrib["name"] == 'Doors' and not doored:
                                    doorIDs = []
                                    for door in property:
                                        doorIDs.append(int(door.attrib["value"]))
                                    doored = True
                                if property.attrib["name"] == 'Color' and not colored:
                                    hexcode = property.attrib["value"].replace('#ff', '')
                                    rgb = tuple(int(hexcode[i:i+2], 16) for i in (0, 2, 4))
                                    colored = True
                        except (TypeError, AttributeError):
                            fail = True
                            print("Error: Failed to load button door list: No 'Doors' or 'Color' property")
                            print(f'Object ID: {object.attrib['gid']}')
                            print("fix you're properties")
                            print("")
                        if not fail:
                            tempButton = Button(x, y, rotation, doorIDs, rgb)
                            self.buttons.append(tempButton)
                    case 33: #locked door
                        tempDoor = Door(x, y, int(object.attrib["id"]))
                        self.objects.append(tempDoor)
                        self.doors.append(tempDoor)
                    case 34: #unlocked door
                        tempDoor = Door(x, y, int(object.attrib["id"]))
                        tempDoor.unlocked = True
                        tempDoor.defaultUnlocked = True
                        self.objects.append(tempDoor)
                        self.doors.append(tempDoor)
                    case 35: #collectable
                        self.coins.append(Collectable(x, y))
                    case 36: #bridge
                        self.objects.append(Bridge(x, y))
                    case _:
                        print("Error: Failed to load object: Unknown object type")
                        print(f'Object ID: {object.attrib['gid']}')
                        print("")

        for button in self.buttons:
            for door in self.doors:
                if door.id in button.connectedDoorIDs:
                    door.color = button.color
                    door.image.fill(door.color)
                    door.image.blit(img_obj, area=(TILESIZE*2, TILESIZE, TILESIZE, TILESIZE))
        for door in self.doors:
            try:
                if door.color != None:
                    pass
            except AttributeError:
                print("Error: Failed to set door color: No connected buttons")
                print(f'Object ID: {object.attrib['gid']}')
                print("Connect a button to this door!")
                door.color = (255, 255, 255)


    def loadEnemies(self):
        tempEnemies = self.enemies
        self.enemies = []
        for enemy in tempEnemies:
            x, y = float(enemy.attrib['x']), float(enemy.attrib['y'])
            type = int(enemy.attrib['gid'])
            match type:
                case 51:
                    self.enemies.append(Enemy(x, y, "evilbrick"))
            

    def parsetmx(self, folder):
        tree = ET.parse(f'{folder}/map.tmx')
        root = tree.getroot()
        for item in root:
            if item.tag == "layer":
                if item.attrib["name"] == "Tiles":
                    mapstr = item.find("data").text
                if item.attrib["name"] == "Background":
                    bgmapstr = item.find("data").text
            if item.tag == "objectgroup":
                if item.attrib["name"] == "Objects":
                    self.objects = item
                if item.attrib["name"] == "Enemies":
                    self.enemies = item
        foundSpawn = False
        for object in self.objects:
            try:
                if int(object.attrib['gid']) == 28:
                    self.spawnPos = (float(object.attrib['x']), float(object.attrib['y']))
                    foundSpawn = True
                    break
            except KeyError:
                pass
        if not foundSpawn:
            print("Error: No spawn point found!")
            print("Please add a spawn object to the object layer of this level,")
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

    def reset(self):
        global playerList
        for coin in self.coins:
            coin.got, coin.gotTimer = False, -1
        playerList[0].coins = 0
        for enemy in self.enemies:
            enemy.reset()
        for door in self.doors:
            door.unlocked = door.defaultUnlocked

    def drawBG(self, player):
        tempBg = pygame.transform.scale(self.bg, (CAM_WIDTH, CAM_HEIGHT))
        player.camera.blit(self.bg, dest=((player.cameraPos[0]/4)%CAM_WIDTH-CAM_WIDTH, 0))
        player.camera.blit(self.bg, dest=((player.cameraPos[0]/4)%CAM_WIDTH, 0))
                    
    def update(self, player):
        self.drawBG(player)
        player.camera.blit(self.bgmapsurf, dest=player.cameraPos)
        player.camera.blit(self.mapsurf, dest=player.cameraPos)
        for object in self.objects:
            object.update(player)
        for coin in self.coins:
            coin.update(player)
        for enemy in self.enemies:
            enemy.update(player)
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
        self.checkpoint = None
        self.maxHP = 3
        self.reset()
        self.camera = pygame.Surface((CAM_WIDTH, CAM_HEIGHT), pygame.SCALED)
        self.fadeLayer = pygame.Surface((CAM_WIDTH, CAM_HEIGHT), pygame.SRCALPHA)
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
        self.coins = 0
        self.onGround = False
        self.canMove = True

    def reset(self):
        global currentMap, playerList
        self.size = 40
        self.playerSprite = pygame.Surface((int(self.size*3/4), self.size), pygame.SRCALPHA)
        self.jumps = [2, 1]
        self.crouching = False
        self.crouchTimer = 0
        self.currentAbility = [None, None]
        self.deathTimer, self.winTimer = 0, -1
        self.offsetX = 0
        self.offsetY = 0
        self.spawnPoint = self.lastCheckpoint
        self.rect = pygame.Rect(self.lastCheckpoint[0], self.lastCheckpoint[1], int(self.size*0.6), int(self.size*0.75))
        self.prevPos = self.rect
        self.cameraPos = (-self.rect[0]+(CAM_WIDTH/2-20), -self.rect[1]-TILESIZE+(CAM_HEIGHT/2-20))
        self.xVel = 0
        self.yVel = 0
        self.grav = 1
        self.speed = 8
        self.coyoteTime = 0
        self.won = False
        self.fadeTime = 0
        self.fadeStart, self.fadeEnd = FADE_O, FADE_T
        self.facing = 1
        self.dead = False
        self.deathType = ''
        self.scoreBonuses = [0, 0, 0, 0] #time, collectables, secret exit, perfect
        self.canMove = True
        self.health = self.maxHP
        self.invuln = 0

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
            if self.crouching:
                self.prevPos = pygame.FRect(self.prevPos[0], self.prevPos[1]-self.size/4, self.prevPos[2], self.prevPos[3]+self.size/4)
                self.rect = pygame.FRect(self.rect[0], self.rect[1]-self.size/4, self.rect[2], self.rect[3]+self.size/4)
                self.crouching = False
            self.setFadeVars(100, 100)
            self.score = int(self.score)
            if self.timer < MINUTE/2:
                self.scoreBonuses[0] = 5000
            elif self.timer < 1*MINUTE:
                self.scoreBonuses[0] = 3000
            elif self.timer < 2*MINUTE:
                self.scoreBonuses[0] = 1000
            elif self.timer < 3*MINUTE:
                self.scoreBonuses[0] = 500
            elif self.timer < 5*MINUTE:
                self.scoreBonuses[0] = 100
            self.scoreBonuses[2] = self.coins*100
            if self.coins == len(currentMap.coins):
                self.scoreBonuses[3] = 5000
            self.won = exitType
            if self.won == 'secret':
                self.scoreBonuses[1] = 1000
            self.canMove = False
            
        allWon = True
        for player in playerList:
            if player.won == False:
                allWon = False
        if allWon and self.winTimer == -1:
            self.winTimer = 1
            currentMap.mus.stop()
            if CLEARMUS:
                mus_clear.play()
            else:
                snd_win.play()
        if self.winTimer > 0:
            self.winTimer += 1
        if self.winTimer > 120 and not any(self.scoreBonuses) and self.fadeTime > 2:
            currentMap.mus.play()
            for player in playerList:
                player.lastCheckpoint = (currentMap.spawnPos[0], currentMap.spawnPos[1]-TILESIZE)
                player.score = 0
                player.timer = 0
                player.checkpoint = None
                player.reset()
                player.setFadeVars(FADE_O, FADE_T)
                player.coins = 0
            currentMap.reset()

            

    def die(self, deathType):
        global playerList
        if len(playerList) == 1:
            currentMap.mus.stop()
        if self.deathTimer == 0:
            if deathType == 'normal':
                snd_spike.stop()
                snd_spike.play()
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
                currentMap.reset()
            self.reset()

    def hurt(self, object):
        if self.invuln == 0:
            if self.health > 0:
                self.health -= 1

            if isinstance(object, Spike):
                snd_spike.play()

            if self.health != 0:
                self.invuln  = -1
                if sideCollide(object, self.rect, 1):
                    self.xVel = 2
                elif sideCollide(object, self.rect, 3):
                    self.xVel = -2
                else:
                    self.xVel = -self.facing*2
                self.yVel = -8
        if self.health == 0:
            if isinstance(object, Spike) or isinstance(object, Enemy):
                self.die('normal')
            else:
                self.die('normal')

    def jump(self):
        if self.yVel < 0:
            jumpMultiplier = (1+abs(self.yVel)/20)
        else:
            jumpMultiplier = 1
        if self.crouching and self.onGround:
            jumpMultiplier = jumpMultiplier*1.5
        self.yVel = -self.grav*10*jumpMultiplier
        if self.currentAbility == ["gp", 1]:
            self.currentAbility = [None, None]
        if self.currentAbility == ["wj", 0]:
            self.currentAbility = ["wj", 1]
            self.facing *= -1

    def setFadeVars(self, start, end):
        self.fadeTime = 0
        self.fadeStart, self.fadeEnd = start, end

    def fade(self):
        self.fadeLayer.set_alpha(pygame.math.lerp(self.fadeStart, self.fadeEnd, ease(self.fadeTime)))
        self.fadeTime += 1/FPS*2
        self.fadeTime = round(self.fadeTime, 2)

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
                self.rect = changePos(self.rect, changeX, 0)
                self.xVel = 0
                colliding = pygame.Rect(self.rect).colliderect(player.rect)
        elif axis == 'y':
            colliding = pygame.Rect(self.rect).colliderect(player.rect)
            if self.yVel < 0:
                changeY = 0.5
            else:
                changeY = -0.5

            while colliding:
                self.rect = changePos(self.rect, 0, changeY)
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

    def singleKeyPress(self, keyIndex):
        pressedKeys = checkKeypress(self.controls)
        pressed, pressedKeys[keyIndex], self.keysDown[keyIndex] = singlePress(pressedKeys[keyIndex], self.keysDown[keyIndex])
        return pressed

    def move(self):
        global currentMap, playerList
        pressedKeys = checkKeypress(self.controls)
        if self.canMove and self.invuln != -1:

            if pressedKeys[1]:
                if self.coyoteTime > 0 and not self.currentAbility[0] == "wj":
                    self.facing = -1
                move = True
                if self.currentAbility[0] == "wj":
                    if self.currentAbility[1] > 0:
                        move = False
                if move:
                    xVelAdd = -self.speed/(self.speed+1)
                else:
                    xVelAdd = 0
                if self.crouching:
                    xVelAdd = -0.2
            elif pressedKeys[3]:
                if self.coyoteTime > 0 and not self.currentAbility[0] == "wj":
                    self.facing = 1
                move = True
                if self.currentAbility[0] == "wj":
                    if self.currentAbility[1] > 0:
                        move = False
                if move:
                    xVelAdd = self.speed/(self.speed+1)
                else:
                    xVelAdd = 0
                if self.crouching:
                    xVelAdd = 0.2
            else:
                xVelAdd = 0

            if self.currentAbility[0] == "wj":
                tempX = self.rect.x
                if self.currentAbility[1] == 0:
                    if self.yVel >= 3:
                        self.yVel = 3
                    if self.singleKeyPress(0) and self.yVel == 3:
                        self.jumps[1] == 0
                        self.jump()
                    if self.onGround:
                        self.currentAbility = [None, None]
                elif 1 <= self.currentAbility[1] <= 10:
                    self.xVel = self.facing*10

                    self.currentAbility[1] += 1
                else:
                    self.currentAbility = [None, None]

            self.xVel += xVelAdd

        if self.rect[0] < 0:
            self.rect = setPos(self.rect, 0, self.rect[1])
            self.xVel = 0

        if self.rect[0]+self.rect[2] > len(currentMap.map[0])*TILESIZE:
            self.rect = setPos(self.rect, len(currentMap.map[0])*TILESIZE-self.rect[2], self.rect[1])
            self.xVel = 0 

        if self.deathType == '' and self.invuln != -1:

            if abs(self.xVel) < self.speed+2:     
                self.xVel *= 0.9
            else:
                if (self.xVel < 0 and xVelAdd < 0) or (self.xVel > 0 and xVelAdd > 0):
                    self.xVel -= xVelAdd
                else:
                    self.xVel *= 0.95
            
            self.anim += abs(self.xVel*1.5/6)/10
            self.frame = int(self.anim)%4

            self.xVel = round(self.xVel, 2)

        if abs(self.xVel) <= 0.05:
            self.xVel = 0
        self.rect = changePos(self.rect, self.xVel, 0)

        if self.canMove:

            if pressedKeys[2]:
                if not self.keysDown[2]:
                    self.keysDown[2] = True
                    if not self.crouching and not self.onGround and self.currentAbility == [None, None]:
                        self.currentAbility = ["gp", 0] #ground pound
                        self.yVel = 10*self.grav
            else:
                self.keysDown[2] = False

        continueCrouching = False
        if self.crouching:
            tempRect = pygame.Rect(self.rect[0], self.rect[1], self.rect[2], self.rect[3]-self.size/4)
            for tiles in getNearbyTiles(self):
                if continueCrouching:
                    break
                if tempRect.colliderect(tiles.rect):
                    continueCrouching = True

            for doors in currentMap.doors:
                if continueCrouching:
                    break
                if tempRect.colliderect(doors.rect) and not doors.unlocked:
                    continueCrouching = True

            for buttons in currentMap.buttons:
                if continueCrouching:
                    break
                if tempRect.colliderect(buttons.rect) or tempRect.colliderect(buttons.rect_button):
                    continueCrouching = True


        if self.yVel <= 0 and self.currentAbility[0] == "gp":
            
            if GROUNDPOUND_PREVENTCROUCH:
                if self.keysDown[2]:
                    self.currentAbility = ["gp", 1]
                else:
                        self.currentAbility = [None, None]
            else:
                self.currentAbility = [None, None]

        if ((pressedKeys[2] and self.onGround) or continueCrouching) and not self.currentAbility == ["gp", 1]:
            self.crouching = True
            self.rect = pygame.FRect(self.rect[0], self.rect[1]+self.size/4, self.rect[2], self.rect[3]-self.size/4)
            self.prevPos = pygame.FRect(self.prevPos[0], self.prevPos[1]+self.size/4, self.prevPos[2], self.prevPos[3]-self.size/4)
        else:
            self.crouching = False
            self.crouchTimer = 0  

            if PLAYERCOLLISION == 1:
                for player in playerList:
                    if player != self and not player.won:
                        self.playerCollide(player, 'x')

        nearbyTiles = getNearbyTiles(self)

        for button in currentMap.buttons:
            if (button.rotation == 1 and self.xVel < 0) or (button.rotation == 3 and self.xVel > 0):
                collide(self, button.rect_button, 'x')
                collide(self, button.rect, 'x')
            else:
                collide(self, button.rect, 'x')
                collide(self, button.rect_button, 'x')

        for door in currentMap.doors:
            if not door.unlocked:
                collide(self, door.rect, 'x')

        wallCollide = False
        for tile in nearbyTiles:
            if not wallCollide:
                wallCollide = collide(self, tile.rect, 'x')
            else:
                collide(self, tile.rect, 'x')

        if wallCollide and not self.onGround:
            if self.currentAbility == [None, None]:
                if pressedKeys[3]:
                    self.facing = 1
                elif pressedKeys[1]:
                    self.facing = -1
            if self.yVel >= 10 and self.currentAbility == [None, None]:         
                self.currentAbility = ["wj", 0]
                self.jumps[1] = 0
        elif not(self.currentAbility[0] == "wj" and self.currentAbility[1] > 1):
            self.currentAbility = [None, None]

        self.yVel += self.grav/2

        if self.canMove and self.singleKeyPress(0) and self.invuln != -1:
            if self.jumps[1] > 0:
                if not self.currentAbility[0] == "wj":
                    if self.coyoteTime > 0 or self.jumps[0]-1 == self.jumps[1]:
                        self.jumps[1] -= 1
                        self.jump()
                    else:
                        if (self.jumps[1] == self.jumps[0]) and self.yVel > 0.5:
                            self.jumps[1] = 0
                            self.jump()
        self.rect = changePos(self.rect, 0, self.yVel)

        if PLAYERCOLLISION == 1:
            for player in playerList:
                if player != self and not player.won:
                    self.playerCollide(player, 'y')

        self.onGround = False

        nearbyTiles = getNearbyTiles(self)
        for button in currentMap.buttons:
            if button.rotation != 0:
                collide(self, button.rect, 'y')
                collide(self, button.rect_button, 'y')
            else:
                collide(self, button.rect_button, 'y')
                collide(self, button.rect, 'y')
            #button.update(self)
        for door in currentMap.doors:
            if not door.unlocked:
                collide(self, door.rect, 'y')
        for obj in currentMap.objects:
            if isinstance(obj, Bridge):
                obj.collide(self)
        for tile in nearbyTiles:
            collide(self, tile.rect, 'y')

        if self.invuln > 0:
            self.invuln -= 1
        if self.invuln == -1 and self.onGround:
            self.invuln = 120

        if self.coyoteTime > 0:
            self.coyoteTime -= 1

    def cameraMove(self):
        global currentMap
        rightCameraBorder = self.rect[0]+int(self.size*3/4) > CAM_WIDTH*0.6-self.cameraPos[0] and self.xVel > 0.75 and self.cameraPos[0] > -(len(currentMap.map[0]))*TILESIZE+CAM_WIDTH
        leftCameraBorder = self.rect[0] < CAM_WIDTH*0.4-self.cameraPos[0] and self.xVel < -0.75 and self.cameraPos[0] < 0
        topCameraBorder = self.rect[1] < CAM_HEIGHT*0.4-self.cameraPos[1] and self.yVel < -0.75 and self.cameraPos[1] < 0
        bottomCameraBorder = self.rect[1]+self.size > CAM_HEIGHT*0.6-self.cameraPos[1] and self.yVel > 0.75 and self.cameraPos[1] > -(len(currentMap.map))*TILESIZE+CAM_HEIGHT

        if leftCameraBorder or rightCameraBorder:
            self.cameraPos = (self.cameraPos[0]-(self.rect[0]-self.prevPos[0]), self.cameraPos[1])
            self.offsetX += (self.rect[0]-self.prevPos[0])

        if topCameraBorder or bottomCameraBorder:
            self.cameraPos = (self.cameraPos[0], self.cameraPos[1]-(self.rect[1]-self.prevPos[1]))
            self.offsetY += (self.rect[1]-self.prevPos[1])

        if self.cameraPos[0] > 0:
            self.offsetX += self.cameraPos[0]
            self.cameraPos = (0, self.cameraPos[1])
        if self.cameraPos[0] < -(len(currentMap.map[0]))*TILESIZE+CAM_WIDTH:
            self.offsetX += self.cameraPos[0]-(-(len(currentMap.map[0]))*TILESIZE+CAM_WIDTH)
            self.cameraPos = (-(len(currentMap.map[0]))*TILESIZE+CAM_WIDTH, self.cameraPos[1])

        if self.cameraPos[1] > 0:
            self.offsetY += self.cameraPos[1]
            self.cameraPos = (self.cameraPos[0], 0)
        if self.cameraPos[1] < -(len(currentMap.map))*TILESIZE+CAM_HEIGHT:
            self.offsetY += self.cameraPos[1]-(-(len(currentMap.map))*TILESIZE+CAM_HEIGHT)
            self.cameraPos = (self.cameraPos[0], -(len(currentMap.map))*TILESIZE+CAM_HEIGHT)

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
            timer, timer_rect = drawText(f'Time: {self.getTime()}')
            score, score_rect = drawText(f'Score: {self.score}')
            coins, coins_rect = drawText(f'CDs: {self.coins}')
            helth, helth_rect = drawText(f'HP: {self.health}/{self.maxHP}')

            timer_rect.topleft = (10, 10)
            score_rect.topright = (CAM_WIDTH-10, 10)
            coins_rect.topleft = (10, 40)
            helth_rect.topleft = (10, 70)

            self.camera.blit(timer, timer_rect)
            self.camera.blit(score, score_rect)
            self.camera.blit(coins, coins_rect)
            self.camera.blit(helth, helth_rect)

            self.camera.blit(self.fadeLayer)
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

                waiting_rect.center = (CAM_WIDTH/2, CAM_HEIGHT/3)
                playersWon_rect.center = (CAM_WIDTH/2, CAM_HEIGHT/7*3)

                self.camera.blit(waiting, waiting_rect)
                self.camera.blit(playersWon, playersWon_rect)

            else:
                if CLEARMUS:
                    delay1, delay2, delay3 = 55, 110, 270
                else:
                    delay1, delay2, delay3 = 40, 50, 120
                self.camera.blit(self.fadeLayer)
                youwin, youwin_rect = drawText('You Won!', font=font_l)
                youwin_rect.center = (CAM_WIDTH/2, pygame.math.lerp(-200, CAM_HEIGHT/8, ease(self.winTimer/30)))
                self.camera.blit(youwin, youwin_rect)

                finalTime, finalTime_rect = drawText(f'Final Time: {self.getTime()}', font_m)
                finalTime_rect.center = (pygame.math.lerp(-200, CAM_WIDTH/2, (self.winTimer-delay1)/30), CAM_HEIGHT*2/8)
                self.camera.blit(finalTime, finalTime_rect)

                score, score_rect = drawText(f'Score: {self.score}', font_m)
                score_rect.center = (pygame.math.lerp(-200, CAM_WIDTH/2, (self.winTimer-delay2)/30), CAM_HEIGHT*3/8)
                self.camera.blit(score, score_rect)  

                timeBonus, timeBonus_rect = drawText(f'Time Bonus: {self.scoreBonuses[0]}', font_s)
                timeBonus_rect.center = (CAM_WIDTH/2, CAM_HEIGHT/14*9)
                self.camera.blit(timeBonus, timeBonus_rect)

                secretExit, secretExit_rect = drawText(f'Secret Exit Bonus: {self.scoreBonuses[1]}', font_s)
                secretExit_rect.center = (CAM_WIDTH/2, CAM_HEIGHT/14*10-10)
                self.camera.blit(secretExit, secretExit_rect)

                coinBonus, coinBonus_rect = drawText(f'CD Bonus: {self.scoreBonuses[2]}', font_s)   
                coinBonus_rect.center = (CAM_WIDTH/2, CAM_HEIGHT/14*11-20)
                self.camera.blit(coinBonus, coinBonus_rect)

                perfectBonus, perfectBonus_rect = drawText(f'Perfect Bonus: {self.scoreBonuses[3]}', font_s)
                perfectBonus_rect.center = (CAM_WIDTH/2, CAM_HEIGHT/14*12-30)
                self.camera.blit(perfectBonus, perfectBonus_rect)

                if checkKeypress([pygame.K_RETURN])[0] and any(self.scoreBonuses) and self.winTimer > delay3:
                    for bonuses in range(len(self.scoreBonuses)):
                        self.score += self.scoreBonuses[bonuses]
                        self.scoreBonuses[bonuses] = 0
                    snd_register.play()
                    self.winTimer = delay3
                    self.setFadeVars(100, FADE_O)
                    self.fadeTime = -4

                if self.winTimer > delay3:
                    if any(self.scoreBonuses):
                        for bonus in range(len(self.scoreBonuses)):
                            if self.scoreBonuses[bonus]:
                                self.scoreBonuses[bonus] -= self.scoreBonuses[bonus] - (self.scoreBonuses[bonus]-50)
                                self.score += self.scoreBonuses[bonus] - (self.scoreBonuses[bonus]-50)

                        if not snd_tally.get_num_channels():
                            snd_tally.play()
                        if not any(self.scoreBonuses):
                            snd_register.play()
                            self.setFadeVars(100, FADE_O)
                            self.fadeTime = -4
                if self.winTimer > delay3 and not any(self.scoreBonuses) and self.fadeTime > 0:
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

            if player.crouching:
                sprite = ((player.frame%2)*30, 80, 30, 40)

            if player.currentAbility == ["gp", 0]:
                sprite = (60, 80, 30, 40)

            if player.currentAbility == ["wj", 0]:
                sprite = (90, 120, 30, 40)

            if player.invuln == -1:
                sprite = (0, 120, 30, 40)

            if player.deathType != '':
                sprite = (90, 40, 30, 40)

            if player.won:
                sprite = (90, 80, 30, 40)

            if not(int(player.invuln/10)%2):
                player.playerSprite.blit(player.spritesheet, area=sprite)

            if player.facing == -1:
                player.playerSprite = pygame.transform.flip(player.playerSprite, True, False)

            if player == self:
                tempRect = getPlayerRect(player, (self.offsetX+self.spawnPoint[0], self.offsetY+self.spawnPoint[1]+TILESIZE))
            else:
                tempRect = getPlayerRect(player, (self.offsetX+self.spawnPoint[0], self.offsetY+self.spawnPoint[1]+TILESIZE))
            tempRect = (tempRect[0]-3, tempRect[1]-10, tempRect[2], tempRect[3])
            self.camera.blit(player.playerSprite, dest=tempRect)

    def update(self):
        global playerList
        self.move()
        if self.deathType == '':
            self.cameraMove()
        if self.deathType != '' and not self.won:
            self.die(self.deathType)
        if self.rect[1] > (len(currentMap.map)+2)*TILESIZE and self.deathType == '' and not self.won:
            self.deathType = 'fell'
        if self.deathType != '' or self.won:
            self.canMove = False
        self.camera.fill((255, 255, 255))
        currentMap.update(self)

        if self.crouching:
            self.prevPos = pygame.FRect(self.prevPos[0], self.prevPos[1]-self.size/4, self.prevPos[2], self.prevPos[3]+self.size/4)
            self.rect = pygame.FRect(self.rect[0], self.rect[1]-self.size/4, self.rect[2], self.rect[3]+self.size/4)

        for button in currentMap.buttons:
            button.update(self)
        if SHOWHITBOXES:
            self.debug_drawRect()
        self.drawPlayer()

        self.prevPos = self.rect
        

        if not self.won and self.deathType == '':
            self.timer += 1

        self.fade()
        self.drawUI()

def setPos(rect, x, y):
    return pygame.FRect(x, y, rect[2], rect[3])

def changePos(rect, x, y):
    return pygame.FRect(round(rect[0] + x, 2), round(rect[1] + y, 2), rect[2], rect[3])

def getNearbyTiles(object):
    global currentMap
    nearbyTiles = []
    xMin, xMax, yMin, yMax =  math.floor(object.rect[0]/TILESIZE-1), math.ceil((object.rect[0]+object.rect[2])/TILESIZE+1), math.floor(object.rect[1]/TILESIZE-1), math.ceil((object.rect[1]+object.rect[3])/TILESIZE+1)

    for row in range(yMin, yMax):
        for tile in range(xMin, xMax):
            try:
                if currentMap.tiles[row][tile] != None and not currentMap.tiles[row][tile].bg:
                    nearbyTiles.append(currentMap.tiles[row][tile])
            except IndexError:
                pass

    return nearbyTiles

def getPlayerRect(player, offsets):
    global currentMap
    return (round(player.rect[0]-offsets[0]+(CAM_WIDTH/2-20), 2), round(player.rect[1]-offsets[1]+(CAM_HEIGHT/2-20), 2), player.rect[2], player.rect[3])

def drawText(textStr, font=font):
    text = font.render(textStr, False, (255, 255, 255))
    text_rect = text.get_rect()
    return text, text_rect

def drawCamera():
    global playerList
    players = len(playerList)
    if players == 1:
        screen.blit(pygame.transform.scale(playerList[0].camera, (WIDTH, HEIGHT)))
    elif players == 2:
        for player in range(len(playerList)):
            screen.blit(pygame.transform.scale(playerList[player].camera, (WIDTH, HEIGHT*0.5)), dest=(0, HEIGHT/2*player))
    elif players == 3:
        for player in range(len(playerList)):
            screen.blit(pygame.transform.scale(playerList[player].camera, (WIDTH*0.5, HEIGHT*0.5)), dest=(WIDTH/4*player, HEIGHT/2*(player%2)))
    elif players == 4:
        for player in range(len(playerList)):
            screen.blit(pygame.transform.scale(playerList[player].camera, (WIDTH*0.5, HEIGHT*0.5)), dest=(WIDTH/2*(player%2), HEIGHT/2*math.floor(player/2)))


def checkKeypress(keyList):
    keys = pygame.key.get_pressed()
    requestedKeys = []
    for key in keyList:
        requestedKeys.append(keys[key])
    return requestedKeys

def singlePress(key, bool):
    press = False
    if key:
        if not bool:
            bool = True
            press = True
    else:
        bool = False
    return press, key, bool

def update():
    global playerList, currentMap
    clock.tick(FPS)

    screen.fill((255, 255, 255))

    for player in playerList:
        player.update()
    
    drawCamera()

    screen2 = pygame.transform.scale(screen, display.get_size())

    display.blit(screen2)

    pygame.display.flip()

currentMap = Map('assets/levels/lv1')

playerList = []
#controls: up, left, down, right
P1 = Player([pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d], 'soday')
P2 = Player([pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT], 'donnie')
P3 = Player([pygame.K_t, pygame.K_f, pygame.K_g, pygame.K_h], 'soday')
P4 = Player([pygame.K_i, pygame.K_j, pygame.K_k, pygame.K_l], 'soday')

def setPlayerList(players):
    global playerList
    if 1 <= players <= 4:
        PLAYERS = players
    else:
        print(f'invalid player amount: {players}')
        return
    playerList = []
    if PLAYERS >= 1:
        playerList.append(P1)
    if PLAYERS >= 2:
        playerList.append(P2)
    if PLAYERS >= 3:
        playerList.append(P3)
    if PLAYERS >= 4:
        playerList.append(P4)

setPlayerList(PLAYERS)

run = True

while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    update()