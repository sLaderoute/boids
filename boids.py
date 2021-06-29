# Start 8:50PM Jun 27 2021
# 10:45PM -- Vision system mostly working. sometimes doesnt work - idk why
# 11:05PM -- Added Boid behaviours basics -- vision still doesnt work for all agents.
#               (everything up to this point done myself)
#               Seems like theres some sort of bias that makes them always head up to the right
# 11:50PM -- Still not really working. Now relies on accelerations to adjust course. I think in order to fix
#               it I will need to look at some example code. Problem for another day


import pygame
import numpy as np
import random
from collections import namedtuple

WIDTH = 500
HEIGHT = 500
N_AGENTS = 30
SIGHT_R = 90
SEPARATION_D = 20
MAX_VEL = 1.5
VELOCITY = MAX_VEL
MAX_STEERING_FORCE = 0.02
SIGHT_ANG = (2*np.pi)*0.33
FPS = 60
Point = namedtuple('Point', 'x y')
Vector = namedtuple('Vector', 'ang mag')


def addVectors(v1, v2):
    v1x = np.cos(v1.ang) * v1.mag
    v1y = np.sin(v1.ang) * v1.mag
    v2x = np.cos(v2.ang) * v2.mag
    v2y = np.sin(v2.ang) * v2.mag
    dy = v2y+v1y
    dx = v1x+v2x
    v = Vector(np.arctan2(dy, dx), np.sqrt(dx**2 + dy**2))
    return v


class Agent:
    def __init__(self, pos, vel, sight_r, sight_ang):
        self.pos = pos
        self.vel = vel
        self.acc = Vector(0, 0)
        self.color = (255, 255, 255)
        self.sight_r = sight_r
        self.sight_ang = sight_ang

    def update(self):
        # update vel based on acceleration
        self.vel = addVectors(self.vel, self.acc)
        if self.vel.mag >= MAX_VEL:
            self.vel = Vector(self.vel.ang, MAX_VEL)
        # move forward
        self.pos = Point((self.pos.x + np.cos(self.vel.ang) * self.vel.mag)%WIDTH, (self.pos.y + np.sin(self.vel.ang) * self.vel.mag)%HEIGHT)
        self.acc = Vector(0, 0)

    def draw(self, pyg, screen):
        scl = 4
        pyg.draw.aaline(screen, self.color, (self.pos.x + np.cos(self.vel.ang) * scl, self.pos.y + np.sin(self.vel.ang) * scl), (self.pos.x +np.cos(self.vel.ang-np.pi*1.25)*scl, self.pos.y + np.sin(self.vel.ang-np.pi*1.25)*scl))

        pyg.draw.aaline(screen, self.color, (self.pos.x + np.cos(self.vel.ang) * scl, self.pos.y + np.sin(self.vel.ang) * scl),
                        (self.pos.x + np.cos(self.vel.ang+np.pi*1.25) * scl, self.pos.y + np.sin(self.vel.ang+np.pi*1.25) * scl))
        pyg.draw.aaline(screen, self.color,
                        (self.pos.x +np.cos(self.vel.ang-np.pi*1.25)*scl, self.pos.y + np.sin(self.vel.ang-np.pi*1.25)*scl),
                        (self.pos.x + np.cos(self.vel.ang + np.pi * 1.25) * scl,
                         self.pos.y + np.sin(self.vel.ang + np.pi * 1.25) * scl))

    def draw_sight(self, pyg, screen):
        rect = (self.pos.x-self.sight_r, self.pos.y-self.sight_r, self.sight_r*2, self.sight_r*2)
        pyg.draw.arc(screen, (255, 255, 0), rect, -self.vel.ang-self.sight_ang/2.0, -self.vel.ang+self.sight_ang/2.0)
        pyg.draw.aaline(screen, (255, 255, 0), (self.pos.x, self.pos.y),
                        (self.pos.x + np.cos(self.vel.ang+self.sight_ang/2.0)*self.sight_r,
                         self.pos.y + np.sin(self.vel.ang+self.sight_ang/2.0)*self.sight_r))
        pyg.draw.aaline(screen, (255, 255, 0), (self.pos.x, self.pos.y), (
                        self.pos.x + np.cos(self.vel.ang - self.sight_ang/2.0) * self.sight_r,
                        self.pos.y + np.sin(self.vel.ang - self.sight_ang/2.0) * self.sight_r))

    def apply_force(self, force):
        self.acc = addVectors(self.acc, force)
        # self.acc = Vector(self.acc.ang, MAX_VEL)

    def can_see(self, other):
        dif_ang = np.arctan2(self.pos.y-other.pos.y, other.pos.x-self.pos.x)
        # print("###")
        # print((360+(180*-self.vel.ang/np.pi))%360)
        # print(180*dif_ang/np.pi)
        # print(180*(((np.pi*2)+(-self.vel.ang-self.sight_ang/2.0))%(np.pi*2))/np.pi)
        # print(180 * (((np.pi*2)+(-self.vel.ang+self.sight_ang/2.0))%(np.pi*2)) / np.pi)
        return np.sqrt(np.power((other.pos.x - self.pos.x), 2) + np.power((other.pos.y - self.pos.y), 2)) < self.sight_r and \
            (((np.pi*2)+(-self.vel.ang-self.sight_ang/2.0))%(np.pi*2) < ((np.pi*2)+dif_ang)%(np.pi*2) < ((np.pi*2)+(-self.vel.ang+self.sight_ang/2.0))%(np.pi*2))

    def cohesion(self, sees):
        if len(sees) == 0:
            return
        x = 0
        y = 0
        for a in sees:
            x += a.pos.x
            y += a.pos.y
        x /= len(sees)
        y /= len(sees)

        # steer towards center of group of visible agents at x,y
        ang = np.arctan2(self.pos.y-y, x-self.pos.x)
        mag = MAX_VEL
        self.apply_force(Vector(ang, mag))

    def alignment(self, sees):
        if len(sees) == 0:
            return
        avg_heading = 0
        for a in sees:
            avg_heading += a.vel.ang
        avg_heading /= len(sees)
        mag = 0.5
        desiredVel = Vector(avg_heading, MAX_VEL)
        self.apply_force(desiredVel)

    def separation(self, sees):
        if len(sees) == 0:
            return
        best_dist = 9999
        closest = sees[0]
        for a in sees:
            cur_dist = np.sqrt((self.pos.x-a.pos.x)**2 + (self.pos.y-a.pos.y)**2)
            if cur_dist < best_dist:
                best_dist = cur_dist
                closest = a
        if best_dist < SEPARATION_D:
            # steer away from closest
            ang = np.arctan2(self.pos.y - closest.pos.y, closest.pos.x - self.pos.x)
            mag = 0.5
            self.apply_force(Vector(ang+180, mag))

    def wiggle(self):
        self.apply_force(Vector((np.pi*random.randint(0, 360)/180), MAX_VEL*0.05))


agents = []
for i in range(N_AGENTS):
    #random.randint(0,628)/100.0
    agents.append(Agent( Point(random.randint(0, WIDTH), random.randint(0, HEIGHT)), Vector(random.randint(0,628)/100.0, VELOCITY), SIGHT_R, SIGHT_ANG ))

pygame.init()
screen = pygame.display.set_mode([WIDTH, HEIGHT])
clock = pygame.time.Clock()

running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))

    for agent in agents:
        sees = []
        for agent2 in agents:
            if agent == agent2:
                continue
            if agent.can_see(agent2):
                sees.append(agent2)
        agent.cohesion(sees)
        agent.alignment(sees)
        agent.separation(sees)

    for agent in agents:
        agent.wiggle()
        agent.update()
        agent.draw(pygame, screen)
        # agent.draw_sight(pygame, screen)
        agent.color = (255,255,255)

    pygame.display.flip()

pygame.quit()
