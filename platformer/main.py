# libraries
import pygame
import math
import random
from os import path

main_folder = path.dirname(__file__)
player_folder = path.join(main_folder, 'player')
idle_folder = path.join(player_folder, 'idle')
run_folder = path.join(player_folder, 'run')
jumping_folder = path.join(player_folder, 'jumping')

pygame.init()
pygame.joystick.init()  # Initializes all joysticks/controllers
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
num_joysticks = len(joysticks)

# create window
# flags = pygame.SCALED | pygame.RESIZABLE
flags = pygame.RESIZABLE
win = pygame.display.set_mode((400, 400), flags, 32)

pygame.display.set_caption("Pygame")

running = True

print("running")

# get window size
w, h = pygame.display.get_surface().get_size()

scaledWH = [1, 1]

playerHeightOffset = 20

# game variables
pixelsPerMeter = 30

renderDist = 8

playerStartDimensions = [20, 40]
playerDimensions = playerStartDimensions

global animFrames
animFrames = {}

font = pygame.font.SysFont("comicsansms", 30)


def blitRotateCenter(surf, image, topleft, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)

    surf.blit(rotated_image, new_rect)


def loadAnimation(filepath, animName, frameDurations):
    global animFrames

    animFrameData = []
    n = 0
    for frame in frameDurations:
        animFrameId = animName + "_" + str(n)
        imgName = animFrameId + ".png"
        imgLoc = path.join(filepath, imgName)
        # imgLoc = path + "/" + animFrameId + ".png"

        animImage = pygame.transform.scale(pygame.image.load(imgLoc).convert_alpha(), (
            int(playerDimensions[0] * scaledWH[0]), int(playerDimensions[1] * scaledWH[1])))
        animFrames[animFrameId] = animImage.copy()
        for i in range(frame):
            animFrameData.append(animFrameId)
        n += 1
    return animFrameData


def loadAnimations():
    animations["run"] = loadAnimation(run_folder, "run", [7, 7])
    animations["idle"] = loadAnimation(idle_folder, "idle", [60, 40])
    animations["jumping"] = loadAnimation(jumping_folder, "jumping", [1])


def changeAction(action, frame, newValue):
    if action != newValue:
        action = newValue
        frame = 0
    return action, frame


animations = {}

loadAnimations()

anim = "idle"
frame = 0
flip = False

# load sprites
background = pygame.image.load(path.join(main_folder, 'scrollingBackground.png')).convert_alpha()
shotgun = pygame.image.load(path.join(main_folder, 'shotgun.png')).convert_alpha()

muzzleFlash = pygame.image.load(path.join(main_folder, 'muzzleFlash.png')).convert_alpha()

robot1 = pygame.image.load(path.join(main_folder, 'robotSprite.png')).convert_alpha()
robot2 = pygame.image.load(path.join(main_folder, 'robotSprite2.png')).convert_alpha()
deadRobot = pygame.image.load(path.join(main_folder, 'deadRobotSprite.png')).convert_alpha()

tentacle1 = pygame.image.load(path.join(main_folder, 'tentacle.png'))
tentacle2 = pygame.image.load(path.join(main_folder, 'tentacle2.png'))

laser = pygame.image.load(path.join(main_folder, 'plasmaBall.png'))

scaledLaser = laser

bossSprites = []
for i in range(5):
    bossSprites.append(pygame.image.load(path.join(main_folder, 'bossSprite_' + str(i) + '.png')).convert_alpha())

scaledBossSprites = []
for i in range(len(bossSprites)):
    scaledBossSprites.append(pygame.transform.scale(bossSprites[i], (
        bossSprites[0].get_size()[0] * scaledWH[1], bossSprites[0].get_size()[1] * scaledWH[1])))

scaledRobot1, scaledRobot2, scaledDeadRobot = robot1, robot2, deadRobot

shotgunWH = [30, 10]
muzzleFlashWH = [30, 20]
scaledShotgun = pygame.transform.scale(shotgun, shotgunWH)
scaledMuzzleFlash = pygame.transform.scale(muzzleFlash, shotgunWH)

pos = [0, 1, 10]
vel = [0, 0]

moveSpeed = 10
groundSpeed = 16

maxGroundSpeed = 5

g = -28
drag = 1
surfaceFriction = 8
jumpForce = 7

shootForce = 30
numBullets = 8
spread = 6
knockback = 4

timescale = 1

maxHealth = 100
health = 100

size = pixelsPerMeter / (pos[2] / pixelsPerMeter)


def mag(vec):
    return (vec[0] ** 2 + vec[1] ** 2) ** (1 / 2)


def normalize(vec):
    return [vec[0] / mag(vec), vec[1] / mag(vec)]


def changeColor(image, color):
    coloredImage = pygame.Surface(image.get_size())
    coloredImage.fill(color)

    finalImage = image.copy()
    finalImage.blit(coloredImage, (0, 0), special_flags=pygame.BLEND_MULT)
    return finalImage


def collisionTest(rect, objects):
    collisionList = []
    for i in objects:
        if rect.colliderect(i.rect):
            collisionList.append(i)
    return collisionList


def move(rect, movement, objects):
    global pos, vel

    collisionDirections = {"up": False, "down": False, "right": False, "left": False}

    pos[0] += movement[0] * dt

    rect.x = w / 2 - playerDimensions[0] - (pos[0] * size / 2)
    rect.y = h / 2 - playerDimensions[1] - (pos[1] * size / 2) + playerHeightOffset

    collisionList = collisionTest(rect, objects)

    for i in collisionList:
        if movement[0] > 0:
            pos[0] = -i.pos[0] + (-rect.width * 2 - i.rect.width) / size
            collisionDirections["right"] = True
        elif movement[0] < 0:
            pos[0] = -i.pos[0] + i.rect.width / size
            collisionDirections["left"] = True
        vel[0] = 0

    pos[1] += movement[1] * dt

    rect.x = w / 2 - playerDimensions[0] - (pos[0] * size / 2)
    rect.y = h / 2 - playerDimensions[1] - (pos[1] * size / 2) + playerHeightOffset

    collisionList = collisionTest(rect, objects)

    for i in collisionList:
        global grounded
        if movement[1] > 0:
            pos[1] = i.pos[1] + (-rect.height * 2 - i.rect.height + playerHeightOffset) / size
            collisionDirections["down"] = True
        elif movement[1] < 0:
            pos[1] = i.pos[1] + (i.rect.height + playerHeightOffset * 2) / size
            collisionDirections["up"] = True
        vel[1] = 0

    return collisionDirections


def rotatePoint(centerPoint, point, angle):
    # rotates a point around a center point by an angle in 2d space

    # convert angle to radians
    angle = math.radians(angle)

    # move point so it can be rotated about the origin
    rotatedPoint = point[0] - centerPoint[0], point[1] - centerPoint[1]

    # rotate about origin
    rotatedPoint = (rotatedPoint[0] * math.cos(angle) -
                    rotatedPoint[1] * math.sin(angle),
                    rotatedPoint[0] * math.sin(angle) +
                    rotatedPoint[1] * math.cos(angle))

    # add original offset
    rotatedPoint = rotatedPoint[0] + centerPoint[0], rotatedPoint[
        1] + centerPoint[1]

    # return result
    return rotatedPoint


entities = []

otherEntities = []


class Bullet():
    def __init__(self, ePos, damage, radius, knockback=5):
        self.pos = ePos
        self.vel = [0, 0]
        self.damage = damage
        self.radius = radius

        self.life = 16

        self.knockback = knockback

        otherEntities.append(self)

    def draw(self):
        global pos

        self.life -= 1
        if self.life <= 0:
            otherEntities.remove(self)

        self.vel = [self.vel[0], self.vel[1] + g * dt]
        self.pos = [self.pos[0] + self.vel[0] * dt, self.pos[1] + self.vel[1] * dt]

        pygame.draw.circle(win, (150, 150, 150), (
            (-self.pos[0] + pos[0]) * size / (pos[2] / 4) * scaledWH[0] + w / 2 * scaledWH[0],
            (-self.pos[1] + pos[1]) * size / (pos[2] / 4) * scaledWH[1] + h / 2 * scaledWH[1]),
                           self.radius * (scaledWH[0] + scaledWH[1]) / 2)


class Laser():
    def __init__(self, ePos, damage, radius, sprite):
        self.pos = ePos
        self.vel = [0, 0]
        self.damage = damage
        self.radius = radius

        self.sprite = pygame.transform.scale(sprite, (radius * 2, radius * 2))

        self.life = 24

        otherEntities.append(self)

    def draw(self):
        global pos

        self.life -= 1
        if self.life <= 0:
            otherEntities.remove(self)

        self.pos = [self.pos[0] + self.vel[0] * dt, self.pos[1] + self.vel[1] * dt]

        win.blit(self.sprite, ((-self.pos[0] + pos[0]) * size / (pos[2] / 4) * scaledWH[0] + w / 2 * scaledWH[0],
                               (-self.pos[1] + pos[1]) * size / (pos[2] / 4) * scaledWH[1] + h / 2 * scaledWH[1]))
        # pygame.draw.circle(win, (255, 0, 0), ((-self.pos[0] + pos[0])*size/(pos[2]/4)*scaledWH[0] + w/2*scaledWH[0], (-self.pos[1] + pos[1])*size/(pos[2]/4)*scaledWH[1] + h/2*scaledWH[1]), self.radius*(scaledWH[0]+scaledWH[1])/2)


class Robot():
    def __init__(self, ePos, health, target, spacing=4, maxSpeed=3, acceleration=5):
        self.pos = ePos
        self.health = health
        self.target = target

        self.acceleration = acceleration
        self.maxSpeed = maxSpeed
        self.spacing = spacing

        self.vel = [0, 0]
        self.dead = False
        self.flip = False
        otherEntities.append(self)

    def draw(self):
        global pos

        if self.dead:
            self.vel = [self.vel[0], self.vel[1] + g * dt]

        self.pos = [self.pos[0] + self.vel[0] * dt, self.pos[1] + self.vel[1] * dt]

        # accelerate towards target
        if not self.dead:
            if mag([self.target.pos[0] - self.pos[0], self.target.pos[1] - self.pos[1]]):
                dir = normalize([self.target.pos[0] - self.pos[0], self.target.pos[1] - self.pos[1]])

                self.vel = [self.vel[0] + dir[0] * dt * self.acceleration,
                            self.vel[1] + dir[1] * dt * self.acceleration]

            # shoot player
            if self.target.following:
                if random.randint(0, .4 // dt) == 0:
                    relPos = [pos[0] - self.pos[0], pos[1] - self.pos[1]]

                    if mag(relPos) > 0:
                        angle = math.degrees(math.atan2(relPos[0], relPos[1])) - 90

                        lsr = Laser(self.pos, 2, 6, pygame.transform.rotate(scaledLaser, angle))

                        shootDir = normalize(relPos)
                        lsr.vel = [shootDir[0] * shootForce, shootDir[1] * shootForce]

            # move away from other bots
            for i in otherEntities:
                if mag([i.pos[0] - self.pos[0], i.pos[1] - self.pos[1]]) > 0:
                    if isinstance(i, Robot) and i != self:
                        dir = normalize([i.pos[0] - self.pos[0], i.pos[1] - self.pos[1]])
                        dist = mag([i.pos[0] - self.pos[0], i.pos[1] - self.pos[1]])
                        if dist < self.spacing and dist != 0:
                            self.vel = [self.vel[0] - dir[0] * dt * (self.spacing - dist),
                                        self.vel[1] - dir[1] * dt * (self.spacing - dist)]
                    elif isinstance(i, Boss):
                        dir = normalize([i.pos[0] - self.pos[0], i.pos[1] - self.pos[1]])
                        dist = mag([i.pos[0] - self.pos[0], i.pos[1] - self.pos[1]])
                        if dist < self.spacing * 2 and dist != 0:
                            self.vel = [self.vel[0] - dir[0] * dt * (self.spacing - dist),
                                        self.vel[1] - dir[1] * dt * (self.spacing * 2 - dist)]

            if mag(self.vel) >= self.maxSpeed:
                self.vel = normalize(self.vel) * self.maxSpeed

            # detect bullets
            for i in otherEntities:
                if isinstance(i, Bullet):
                    if ((i.pos[0] - self.pos[0]) ** 2 + (i.pos[1] - self.pos[1]) ** 2) ** (1 / 2) < .6:
                        self.health -= i.damage
                        if self.health <= 0:
                            self.dead = True
                            global health
                            health += 10

                        dir = [self.pos[0] - i.pos[0], self.pos[1] - i.pos[1]]
                        self.vel = [self.vel[0] + dir[0] * i.knockback, self.vel[1] + dir[1] * i.knockback]

                        otherEntities.remove(i)

        if frame % 2 == 0:
            sprite = scaledRobot1
        else:
            sprite = scaledRobot2
        if self.dead:
            sprite = scaledDeadRobot

        if pos[0] + .2 < self.pos[0]:
            self.flip = False
        elif pos[0] - .2 > self.pos[0]:
            self.flip = True

        win.blit(pygame.transform.flip(sprite, self.flip, False), (
            (-self.pos[0] + pos[0]) * size / (pos[2] / 4) * scaledWH[0] + w / 2 * scaledWH[0],
            (-self.pos[1] + pos[1]) * size / (pos[2] / 4) * scaledWH[1] + h / 2 * scaledWH[1]))


class Boss():
    def __init__(self, ePos, health, activeDist=8, spacing=4, maxSpeed=3, acceleration=5, distToPlayer=8):
        self.pos = ePos
        self.health = health
        self.maxHealth = health

        self.acceleration = acceleration
        self.maxSpeed = maxSpeed
        self.spacing = spacing

        self.distToPlayer = distToPlayer

        self.activeDist = activeDist

        self.vel = [0, 0]
        self.dead = False
        self.flip = False
        self.rot = 0
        self.f = 0
        self.heads = 5
        self.following = False
        otherEntities.append(self)

    def draw(self):
        global pos

        if self.dead:
            self.vel = [self.vel[0], self.vel[1] + g * dt]

        self.pos = [self.pos[0] + self.vel[0] * dt, self.pos[1] + self.vel[1] * dt]

        if not self.dead:
            # accelerate towards target
            dist = mag([pos[0] - self.pos[0], pos[1] - self.pos[1]])
            if dist < self.activeDist:
                self.following = True
                self.activeDist = 30
                dir = normalize([pos[0] - self.pos[0], pos[1] - self.pos[1]])
                self.vel = [self.vel[0] + dir[0] * dt * self.acceleration,
                            self.vel[1] + dir[1] * dt * self.acceleration]

            # shoot player
            if self.following:
                if random.randint(0, .4 // dt) == 0:
                    relPos = [pos[0] - self.pos[0], pos[1] - self.pos[1]]

                    if mag(relPos) > 0:
                        angle = math.degrees(math.atan2(relPos[0], relPos[1])) - 90

                        lsr = Laser(self.pos, 4, 12, pygame.transform.rotate(scaledLaser, angle))

                        shootDir = normalize(relPos)
                        lsr.vel = [shootDir[0] * shootForce, shootDir[1] * shootForce]

            self.vel = [self.vel[0] * (1 - .4 * dt), self.vel[1] * (1 - .4 * dt)]

            # move away from other bots
            for i in otherEntities:
                if isinstance(i, Robot) and i != self:
                    dir = normalize([i.pos[0] - self.pos[0], i.pos[1] - self.pos[1]])
                    dist = mag([i.pos[0] - self.pos[0], i.pos[1] - self.pos[1]])
                    if dist < self.spacing and dist != 0:
                        self.vel = [self.vel[0] - dir[0] * dt * (self.spacing - dist),
                                    self.vel[1] - dir[1] * dt * (self.spacing - dist)]

            # move away from player
            dir = normalize([pos[0] - self.pos[0], pos[1] - self.pos[1]])
            dist = mag([pos[0] - self.pos[0], pos[1] - self.pos[1]])
            if dist < self.distToPlayer and dist != 0:
                self.vel = [self.vel[0] - dir[0] * dt * (self.distToPlayer - dist),
                            self.vel[1] - dir[1] * dt * (self.distToPlayer - dist)]

            if mag(self.vel) >= self.maxSpeed:
                self.vel = normalize(self.vel) * self.maxSpeed

            for i in otherEntities:
                if isinstance(i, Bullet):
                    if ((i.pos[0] - self.pos[0]) ** 2 + (i.pos[1] - self.pos[1]) ** 2) ** (1 / 2) < .6:
                        self.health -= i.damage
                        if self.health <= 0:
                            self.heads -= 1
                            if self.heads > 0:
                                head = Robot([self.pos[0] + 1, self.pos[1]], 20, self)

                            self.health = self.maxHealth
                            if self.heads < 0:
                                self.dead = True
                                print("BOSS WIN!", timer)

                        otherEntities.remove(i)

        self.f += 1
        random.seed(self.f // 6)
        sprite = scaledBossSprites[random.randint(0, len(bossSprites) - 1)]

        if self.dead:
            sprite = scaledDeadRobot

        if pos[0] + .2 < self.pos[0]:
            self.flip = False
        elif pos[0] - .2 > self.pos[0]:
            self.flip = True

        # Boss eye
        win.blit(sprite, ((-self.pos[0] + pos[0]) * size / (pos[2] / 4) * scaledWH[0] + w / 2 * scaledWH[0] -
                          scaledBossSprites[0].get_size()[1] / 2,
                          (-self.pos[1] + pos[1]) * size / (pos[2] / 4) * scaledWH[1] + h / 2 * scaledWH[1] -
                          scaledBossSprites[0].get_size()[1] / 2))

        if frame % 2 == 0:
            sprite = scaledRobot1
        else:
            sprite = scaledRobot2
        if self.dead:
            sprite = scaledDeadRobot

        if self.heads > 0:
            a = (2 * math.pi) / self.heads
            radius = size / 2 * scaledWH[1]

            self.rot += (2 * math.pi) * dt / self.heads

            # Heads
            for i in range(self.heads):
                angle = a * i + self.rot
                win.blit(pygame.transform.flip(sprite, self.flip, False), (
                    (-self.pos[0] + pos[0]) * size / (pos[2] / 4) * scaledWH[0] + w / 2 * scaledWH[0] + math.cos(
                        angle) * radius - scaledRobot1.get_size()[0] / 2,
                    (-self.pos[1] + pos[1]) * size / (pos[2] / 4) * scaledWH[1] + h / 2 * scaledWH[1] + math.sin(
                        angle) * radius - scaledRobot1.get_size()[1] / 2))


class Target():
    def __init__(self, ePos, radius, activeDist=8, maxSpeed=3, acceleration=5):
        self.pos = ePos
        self.vel = [0, 0]
        self.radius = radius
        self.acceleration = acceleration
        self.maxSpeed = maxSpeed
        self.activeDist = activeDist

        self.following = False

        otherEntities.append(self)

    def draw(self):
        global pos

        self.pos = [self.pos[0] + self.vel[0] * dt, self.pos[1] + self.vel[1] * dt]

        dist = mag([pos[0] - self.pos[0], pos[1] - self.pos[1]])
        dir = normalize([pos[0] - self.pos[0], pos[1] - self.pos[1]])

        m = 1
        if self.following:
            m = 2

        if dist <= self.activeDist * m:
            self.following = True
            self.vel = [self.vel[0] + dir[0] * dt * self.acceleration, self.vel[1] + dir[1] * dt * self.acceleration]
        else:
            self.following = False
            self.vel = [self.vel[0] * (1 - .1 * dt), self.vel[1] * (1 - .1 * dt)]

        if mag(self.vel) >= self.maxSpeed:
            self.vel = normalize(self.vel) * self.maxSpeed

        # pygame.draw.circle(win, (255, 0, 0), ((-self.pos[0] + pos[0])*size/(pos[2]/4)*scaledWH[0] + w/2*scaledWH[0], (-self.pos[1] + pos[1])*size/(pos[2]/4)*scaledWH[1] + h/2*scaledWH[1]), self.radius*(scaledWH[0]+scaledWH[1])/2)


def makeSwarm(sPos, n):
    t = Target(sPos, 5)

    a = (2 * math.pi) / n
    r = n / (2 * math.pi)
    for i in range(n):
        rb = Robot([sPos[0] + math.cos(a * i) * r, sPos[1] + math.sin(a * i) * r], 30, t)


renderQueue = []


class Object3D():
    def __init__(self, ePos):
        self.pos = ePos
        entities.append(self)

    def draw(self):
        points = []

        # calculate screen position of verts
        for i in self.verts:
            # move
            p = [i[0] - self.pos[0] - pos[0], i[1] + self.pos[1] - pos[1], i[2] - pos[2]]

            scale = pixelsPerMeter / (p[2] / pixelsPerMeter)
            p = [p[0] * scale, p[1] * scale, p[2]]

            # add r to points list
            points.append(p)

        # draw edges
        """for i in self.edges:
            # get points of edge
            p1 = points[i[0]]
            p2 = points[i[1]]

            # draw
            pygame.draw.line(
                win, (0, min(max(255 - (p1[2] + p2[2]) / 2 * -20, 10), 255), 0),
                (w / 2 + p1[0] / 2,
                 h / 2 + p1[1] / 2),
                (w / 2 + p2[0] / 2,
                 h / 2 + p2[1] / 2), 2)"""

        for face in self.faces:
            ps = []
            for iNum, i in enumerate(face):
                if iNum > 0:
                    ps.append((w / 2 + points[i][0] / 2, h / 2 + points[i][1] / 2))

            averagePos = [0, 0, 0]
            for iNum, i in enumerate(ps):
                averagePos = [averagePos[0] + i[0] / len(ps), averagePos[1] + i[1] / len(ps),
                              averagePos[2] + (points[face[iNum + 1]][2] + pos[2]) / len(ps)]

            lighting = (face[0] / 255)
            renderQueue.append((((averagePos[0] - w / 2) ** 2 + (averagePos[1] - h / 2) ** 2) ** (1 / 2),
                                (self.color[0] * lighting, self.color[1] * lighting, self.color[2] * lighting), ps,
                                averagePos[2]))

        # draw points on top of edges
        """for i in points:
            pygame.draw.circle(win, (255, 255, 0),
                               (w / 2 + i[0] / 2,
                                h / 2 + i[1] / 2), 2)"""


class Cube(Object3D):
    def __init__(self, ePos, scale):
        self.pos = ePos
        self.scale = scale
        self.color = (0, 0, random.randint(140, 220))

        # run parent init function
        super(Cube, self).__init__(self.pos)

        # define vertices of tesseract
        self.verts = [
            # cube1
            [-1, -1, -1],
            [1, -1, -1],
            [-1, 1, -1],
            [1, 1, -1],
            [-1, -1, 1],
            [1, -1, 1],
            [-1, 1, 1],
            [1, 1, 1]
        ]

        for vNum, v in enumerate(self.verts):
            for dNum, d in enumerate(v):
                self.verts[vNum][dNum] = d * scale[dNum]

        # define edges of tesseract
        self.edges = [
            # cube1 edges
            [0, 1],
            [0, 2],
            [0, 4],
            [1, 3],
            [3, 2],
            [3, 7],
            [7, 6],
            [6, 4],
            [6, 2],
            [5, 7],
            [5, 4],
            [5, 1]
        ]

        self.faces = [
            [200, 6, 2, 0, 4],
            [130, 1, 3, 7, 5],
            [100, 0, 1, 5, 4],
            [255, 2, 3, 7, 6],
            [160, 6, 7, 5, 4]
        ]

        size = pixelsPerMeter / (pos[2] / pixelsPerMeter)

        self.rect = pygame.Rect((int(w / 2 + self.pos[0] * size / 2 - self.scale[0] * size / 2),
                                 int(h / 2 - self.pos[1] * size / 2 - self.scale[1] * size / 2),
                                 self.scale[0] * pixelsPerMeter / (pos[2] / pixelsPerMeter), self.scale[1] * size))


# instantiate cubes
cube = Cube([0, 0], [2, .2, 2])
cube = Cube([6, .5], [1.5, .2, 1])
cube = Cube([12, -.5], [1.5, .2, 1.5])
cube = Cube([20, -.5], [3, .25, 3])
cube = Cube([22.5, .25], [.5, .5, 1])
cube = Cube([25, -2.3], [.5, 4, 1])
cube = Cube([29, -3.4], [.75, 5.5, .75])
cube = Cube([34.5, -6.2], [.6, 5.5, .6])
cube = Cube([38, -6], [.4, 5.5, .4])
cube = Cube([41, -1.25], [.4, .25, .4])
cube = Cube([46, -1.25], [2, 1, 1])
cube = Cube([52, -1], [2.2, .8, .2])
cube = Cube([58, -.8], [2, .8, .25])

makeSwarm([-18, 4], 2)
makeSwarm([-38, 2], 3)
makeSwarm([-48, 3], 5)

boss = Boss([-58, 1], 200)

scaledBackground = pygame.transform.scale(background, (int(w * 2), int(h / 2)))
scaledBackground = changeColor(scaledBackground, (200, 0, 150))

scaledBackground2 = pygame.transform.flip(background, True, False)
scaledBackground2 = pygame.transform.scale(scaledBackground2, (w, h // 4))
scaledBackground2 = changeColor(scaledBackground2, (150, 0, 100))

timer = 0

# pygame clock
clock = pygame.time.Clock()

grounded = True
collisions = {"up": False, "down": False, "right": False, "left": False}
while running:
    shoot = False
    scaledWH = [pygame.display.get_surface().get_size()[0] / w, pygame.display.get_surface().get_size()[1] / h]
    # Get Delta Time
    fps = clock.get_fps()
    if fps == 0:
        fps = 60
    dt = (1 / fps) * timescale

    rstickPos = None
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            shoot = True
        if event.type == pygame.JOYBUTTONDOWN:
            if joysticks[0].get_button(5):
                shoot = True
        if event.type == pygame.VIDEORESIZE:
            scaledWH = [pygame.display.get_surface().get_size()[0] / w, pygame.display.get_surface().get_size()[1] / h]
            # scaledWH = [1, 1]
            whRatio = ((scaledWH[0] / scaledWH[1]) + 1) / 2
            playerDimensions = [int(playerStartDimensions[0] * (1 / whRatio)), int(playerStartDimensions[1] * whRatio)]

            scaledBackground = pygame.transform.scale(background, (int(w * 2 * scaledWH[0]), int(h / 2 * scaledWH[1])))
            scaledBackground = changeColor(scaledBackground, (200, 0, 150))

            scaledBackground2 = pygame.transform.flip(background, True, False)
            scaledBackground2 = pygame.transform.scale(scaledBackground2,
                                                       (int(w * scaledWH[0]), int(h / 4 * scaledWH[1])))
            scaledBackground2 = changeColor(scaledBackground2, (150, 0, 100))

            loadAnimations()
            scaledShotgun = pygame.transform.scale(shotgun, (
                int(shotgunWH[0] * scaledWH[0]), int(shotgunWH[1] * scaledWH[1])))
            scaledMuzzleFlash = pygame.transform.scale(muzzleFlash, (
                int(muzzleFlashWH[0] * scaledWH[0]), int(muzzleFlashWH[1] * scaledWH[1])))

            scaledRobot1 = pygame.transform.scale(robot1, (
                int(robot1.get_size()[0] * scaledWH[1]), int(robot1.get_size()[1] * scaledWH[1])))
            scaledRobot2 = pygame.transform.scale(robot2, (
                int(robot2.get_size()[0] * scaledWH[1]), int(robot2.get_size()[1] * scaledWH[1])))
            scaledDeadRobot = pygame.transform.scale(deadRobot, (
                int(deadRobot.get_size()[0] * scaledWH[1]), int(deadRobot.get_size()[1] * scaledWH[1])))

            scaledBossSprites = []
            for i in range(len(bossSprites)):
                scaledBossSprites.append(pygame.transform.scale(bossSprites[i], (
                    int(bossSprites[0].get_size()[0] * scaledWH[1]), int(bossSprites[0].get_size()[1] * scaledWH[1]))))

            scaledTentacle1 = pygame.transform.scale(tentacle1, (
                int(tentacle1.get_size()[0] * scaledWH[1]), int(tentacle1.get_size()[1] * scaledWH[1])))
            scaledTentacle2 = pygame.transform.scale(tentacle2, (
                int(tentacle2.get_size()[0] * scaledWH[1]), int(tentacle2.get_size()[1] * scaledWH[1])))

            scaledLaser = pygame.transform.scale(laser, (
                int(laser.get_size()[0] * scaledWH[1]), int(laser.get_size()[1] * scaledWH[1])))

    # get keys pressed
    keys = pygame.key.get_pressed()

    # move

    speed = moveSpeed
    if grounded and abs(vel[0]) < maxGroundSpeed:
        speed = groundSpeed

    if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and not grounded:
        vel[1] -= moveSpeed * dt

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        vel[0] += speed * dt
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        vel[0] -= speed * dt

    playerRect = pygame.Rect((w // 2 - playerDimensions[0] - int(pos[0] * size / 2),
                              h // 2 - playerDimensions[1] - int(pos[1] * size / 2) + playerHeightOffset,
                              playerDimensions[0],
                              playerDimensions[1]))

    point1 = [w / 2 - pos[0] * size / 2 - 2, h / 2 + 1 - pos[1] * size / 2 + playerHeightOffset]
    point2 = [w / 2 - pos[0] * size / 2 - playerRect.width + 2, h / 2 + 1 - pos[1] * size / 2 + playerHeightOffset]
    grounded = False
    for i in entities:
        collision = i.rect.collidepoint(point1)
        collision = collision or i.rect.collidepoint(point2)
        if collision:
            grounded = True

    for i in otherEntities:
        if isinstance(i, Laser):
            collision = playerRect.collidepoint([w / 2 - i.pos[0] * size / 2, h / 2 - i.pos[1] * size / 2])
            if collision:
                health -= i.damage

                otherEntities.remove(i)

    if not grounded:
        # gravity
        vel = [vel[0], vel[1] + g * dt]

    # drag
    vel = [vel[0] * (1 - drag * dt), vel[1] * (1 - drag * dt)]

    collisions = move(playerRect, vel, entities)

    # surface friction
    if grounded:
        v = vel[0]

        if v > 0:
            v = max(v - surfaceFriction * dt, 0)
        elif v < 0:
            v = min(v + surfaceFriction * dt, 0)

        vel = [v, vel[1]]

    if (keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]) and grounded:
        vel[1] += jumpForce

    if pygame.joystick.get_init:
        if num_joysticks > 0:
            stick = joysticks[0]
            # hat_state = stick.get_hat(0)
            # vel[0] += hat_state[0] * speed * dt
            # vel[1] += hat_state[1] * -speed * dt
            stick_x = stick.get_axis(0)
            stick_y = stick.get_axis(1)
            rstickPos = [stick.get_axis(3), stick.get_axis(4)]
            # stick_y = stick.get_axis(1)
            deadzone = 0.2
            if abs(stick_x) > deadzone:
                vel[0] += stick_x * -speed * dt
            jumpdeadzone = 0.4
            if (abs(stick_y) > jumpdeadzone) and grounded:
                vel[1] += jumpForce
            # if abs(stick_y) > deadzone:
            #    player.vel.y += stick_y * player.player_acc
            # b1 = stick.get_button(1)
            # b2 = stick.get_button(2)
            # b3 = stick.get_button(3)
            # b5 = stick.get_button(5)
            # if stick.get_button(0) and grounded:
            #    vel[1] += jumpForce

    # clear screen
    win.fill((0, 0, 5))

    # background
    xPos = pos[0] * size / 6
    spacing = w * 8
    farX = -int(xPos / spacing - .5)
    win.blit(scaledBackground2,
             ((xPos / 4 + farX * (spacing / 4)) * scaledWH[0], (3 * h / 8 + pos[1] / 4 * size / 6) * scaledWH[1]))

    win.blit(scaledBackground,
             ((xPos / 2 + farX * (spacing / 2)) * scaledWH[0], (h / 4 + pos[1] / 2 * size / 6) * scaledWH[1]))

    mousePos = pygame.mouse.get_pos()
    point = [mousePos[0] - pos[0] * size / 2, mousePos[1] - pos[1] * size / 2]

    # draw cube
    for i in entities:
        if i.pos[0] > -pos[0] - renderDist and i.pos[0] < -pos[0] + renderDist:
            i.draw()

        # debug

        """collision = i.rect.collidepoint(point)
        if collision:
            pygame.draw.rect(win, (255, 0, 0), (w / 2 + i.pos[0] * size / 2 + pos[0] * size / 2 - i.scale[0] * size / 2,
                                                h / 2 - i.pos[1] * size / 2 + pos[1] * size / 2 - i.scale[1] * size / 2,
                                                i.scale[0] * pixelsPerMeter / (pos[2] / pixelsPerMeter),
                                                i.scale[1] * size))"""

    orderedQueue = []
    frontFaces = []

    for i in range(len(renderQueue)):
        closest = renderQueue[0]
        for r in renderQueue:
            if r[0] > closest[0]:
                closest = r
        inFront = False
        for r in renderQueue:
            if r[3] > 0:
                closest = r
                inFront = True
        renderQueue.remove(closest)
        if not inFront:
            orderedQueue.append(closest)
        else:
            frontFaces.append(closest)

    for i in orderedQueue:
        ps = []
        for point in i[2]:
            ps.append((point[0] * scaledWH[0], point[1] * scaledWH[1]))
        pygame.draw.polygon(win, i[1], ps)
    for i in frontFaces:
        ps = []
        for point in i[2]:
            ps.append((point[0] * scaledWH[0], point[1] * scaledWH[1]))
        pygame.draw.polygon(win, i[1], ps)

    renderQueue = []

    # player
    if grounded:
        if vel[0] > 0:
            anim, frame = changeAction(anim, frame, "run")
        elif vel[0] < 0:
            anim, frame = changeAction(anim, frame, "run")
        else:
            anim, frame = changeAction(anim, frame, "idle")
    else:
        anim, frame = changeAction(anim, frame, "jumping")

    mousePos = pygame.mouse.get_pos()
    flipped = False
    if rstickPos:
        if rstickPos[0] < 0 and not flip:
            flip = True
            flipped = True
        elif rstickPos[0] > 0 and flip:
            flip = False
            flipped = True
    else:
        if mousePos[0] < w / 2 * scaledWH[0] and not flip:
            flip = True
            flipped = True
        elif mousePos[0] > w / 2 * scaledWH[0] and flip:
            flip = False
            flipped = True

    if flipped:
        anim, frame = changeAction(anim, frame, "idle")
        frame = 61

    frame += 1
    if frame >= len(animations[anim]):
        frame = 0
    playerImgId = animations[anim][frame]
    playerImg = animFrames[playerImgId]

    win.blit(pygame.transform.flip(playerImg, flip, False), (
        (w / 2 - playerDimensions[0]) * scaledWH[0], (h / 2 - playerDimensions[1] + playerHeightOffset) * scaledWH[1]))

    # Shooting
    if not rstickPos:
        relPos = [mousePos[0] - w / 2 * scaledWH[0], mousePos[1] - h / 2 * scaledWH[1]]
    else:
        relPos = rstickPos

    angle = math.degrees(math.atan2(relPos[0], relPos[1])) - 90

    rotatedShotgun = pygame.transform.flip(scaledShotgun, False, flip)
    flipOffset = 0
    if flip:
        flipOffset = -playerDimensions[0] / 2

    shotgunPos = ((w / 2 - playerDimensions[0] + flipOffset) * scaledWH[0], h / 2 * scaledWH[1])
    blitRotateCenter(win, rotatedShotgun, shotgunPos, angle)

    shootDir = rotatePoint((0, 0), (0, 1), -angle + 90)

    if shoot:
        blitRotateCenter(win, scaledMuzzleFlash,
                         ((w / 2 + flipOffset - playerDimensions[0] - shootDir[0] * shotgunWH[0]) * scaledWH[0],
                          (h / 2 - 10) * scaledWH[1] - shootDir[1] * shotgunWH[0] * scaledWH[0]), angle)

        for i in range(numBullets):
            bullet = Bullet([pos[0] + shootDir[0] / 2, pos[1] + shootDir[1] / 2], 5, 1)
            bullet.vel = [shootDir[0] * shootForce + random.randint(-spread, spread),
                          shootDir[1] * shootForce + random.randint(-spread, spread)]

        m = 1
        if grounded:
            m = .5
        vel = [vel[0] - shootDir[0] * knockback * m, vel[1] - shootDir[1] * knockback * m]

    # draw robots
    for i in otherEntities:
        i.draw()

    # UI
    pygame.draw.rect(win, (100, 0, 0), (8, h * scaledWH[1] - 12 - 20, 164, 24))
    pygame.draw.rect(win, (255, 0, 0), (10, h * scaledWH[1] - 10 - 20, (health / maxHealth) * 160, 20))

    health = min(health, maxHealth)

    if pos[1] < -15:
        health -= 100 * dt

    if health <= 0:
        print("you died")
        timescale = 0
        running = False

    n = 0
    for i in otherEntities:
        if isinstance(i, Robot):
            n += 1
        if isinstance(i, Boss):
            n += 1

    if n == 0:
        print("Enemy Win!")
        timescale = 0

    # Timer
    timer += dt
    text = font.render(str(round(timer, 2)), True, (0, 0, 255))
    win.blit(text,
             (w * scaledWH[0] - text.get_width() - 10, text.get_height()))

    # update display
    pygame.display.update()

    # limit fps to 60
    clock.tick(60)

pygame.quit()
