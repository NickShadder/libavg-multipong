'''
Created on 15.02.2012

@author: 2526240
'''

import random
import math
from config import PPM, pointsToWin, ballRadius, ghostRadius
from libavg import avg, ui
from Box2D import b2EdgeShape, b2PolygonShape, b2FixtureDef, b2CircleShape

cats = {'border':0x0001, 'ghost':0x0002, 'ball':0x0004, 'brick':0x0008}
def collideWith(categories):
    return reduce(lambda x, y: x | y, [cats[el] for el in categories])

standardXInertia = 20*ballRadius # XXX solve more elegantly 

class GameObject:
    def __init__(self, renderer, world):
        self.renderer = renderer
        self.world = world
        self.renderer.register(self)
        
    def destroy(self):
        self.renderer.deregister(self)
        if self.body is not None:
            self.world.DestroyBody(self.body)
            self.body = None
        if self.node is not None:
            self.node.active = False
            self.node.unlink(True)
            self.node = None
    
class Ball(GameObject):
    def __init__(self, renderer, world, parentNode, position, leftPlayer, rightPlayer, radius=ballRadius):
        GameObject.__init__(self, renderer, world)
        self.spawnPoint = parentNode.pivot/PPM # XXX maybe make a static class variable
        self.leftPlayer = leftPlayer
        self.rightPlayer = rightPlayer
        self.lastPlayer = None
        diameter = 2 * radius * PPM
        svg = avg.SVG('../data/img/char/pacman.svg', False)
        self.node = svg.createImageNode('layer1', dict(parent=parentNode), (diameter, diameter))
        d = {'type':'body', 'node':self.node,'obj':self}
        self.body = world.CreateDynamicBody(position=position, userData=d)
        self.body.CreateCircleFixture(radius=radius, density=1, restitution=1,
                                      friction=.01, groupIndex = 1, categoryBits=cats['ball'],
                                      userData='ball')
        self.body.CreateCircleFixture(radius=radius, userData='ball',isSensor=True)
        self.nudge()
        self.node.setEventHandler(avg.CURSORDOWN,avg.TOUCH,lambda e:self.reSpawn()) # XXX remove

    def reSpawn(self,pos=None):
        if pos is None:
            pos = self.spawnPoint
        self.body.position=pos
        yOffset = random.randint(-10,10)
        direction = (-standardXInertia,yOffset) if  self.leftPlayer.points > self.rightPlayer.points else (standardXInertia,yOffset)
        self.nudge(direction)
    
    def zone(self):
        lz,rz = self.leftPlayer.zone,self.rightPlayer.zone        
        if lz.getAbsPos((0,0))[0] < self.node.pos[0] < lz.getAbsPos(lz.size)[0]:
            return self.leftPlayer
        elif rz.getAbsPos((0,0))[0] < self.node.pos[0] < rz.getAbsPos(rz.size)[0]:
            return self.rightPlayer
        else:
            return None        
        
    def nudge(self, direction=None):
        self.body.angularVelocity=0
        self.body.angle = 0
        if direction is None:
            direction = (random.choice([standardXInertia,-standardXInertia]),random.randint(-10,10)) 
        self.body.linearVelocity=direction
        
class Player:
    def __init__(self, game, avgNode):
        self.points = 0
        self.other = None
        self.game = game
        self.zone = avgNode
        
        left = avgNode.pos == (0, 0)         
        angle = math.pi / 2 if left else -math.pi / 2 
        pos = (avgNode.width, 2) if left else (0, avgNode.height - 2)            
        # XXX gameobects may obstruct view of the points!
        self.pointsDisplay = avg.WordsNode(parent=avgNode, pivot=(0, 0), pos=pos, angle=angle,
                                           text='Points: 0 / %d' % pointsToWin)
    
    def addPoint(self, points=1):
        self.points += points
        self.updateDisplay()
        if self.points >= pointsToWin:
            self.game.win(self)

    def removePoint(self, points=1):
        self.points -= points
        if self.points < 0:
            self.points = 0
        self.updateDisplay()
    
    def updateDisplay(self):
        self.pointsDisplay.text = 'Points: %d / %d' % (self.points, pointsToWin)
        

class Ghost(GameObject):
    def __init__(self, renderer, world, parentNode, position, name, mortality=0, radius=ghostRadius):
        GameObject.__init__(self, renderer, world)
        self.parentNode = parentNode
        self.spawnPoint = position
        self.name = name
        self.mortal = mortality
        self.diameter = 2 * radius * PPM
        self.node = avg.ImageNode(parent=parentNode, size=(self.diameter, self.diameter))
        self.setBitmap(name)
        d = {'type':'body', 'node':self.node,'obj':self}
        ghostUpper = b2FixtureDef(userData='ghost',shape=b2CircleShape(radius=radius),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'])
        ghostLower = b2FixtureDef(userData='ghost',shape=b2PolygonShape(box=(radius, radius / 2, (0, -radius / 2), 0)),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'])
        self.body = world.CreateDynamicBody(position=position, fixtures=[ghostUpper, ghostLower],
                                            userData=d, fixedRotation=True) # XXX let them rotate after we fixed their propulsion
        ui.DragRecognizer(self.node, moveHandler=self.onMove) # XXX just for debugging and fun
        
        # XXX I don't like this...        
        self.direction = (8000, 10) # XXX what is this?!
        self.body.ApplyForce(force=(self.direction[0], self.direction[1]), point=self.body.position)
    
    def onMove(self, event, offset):
        self.body.position = event.pos / PPM
            
    def flipState(self):
        self.setBitmap(self.name if self.mortal else 'blue')
        self.mortal ^= 1
        
    def setBitmap(self, name):
        svg = avg.SVG('../data/img/char/' + name + '.svg', False)        
        self.node.setBitmap(svg.renderElement('layer1', (self.diameter, self.diameter)))        

    def reSpawn(self,pos=None):
        if pos is None:
            pos = self.spawnPoint
        self.body.position = pos
        self.setBitmap(self.name) # ghost respawns in immortal state XXX change this?
        self.mortal = 0
    
    # TODO refactor from here
    def setDir(self, s):
        self.body.ApplyForce(force=((-1) * self.direction[0], (-1) * self.direction[1]), point=self.body.position)
        if s == "left":
            self.direction = (8000, self.direction[1])   
        else:
            self.direction = (-8000, self.direction[1])
        self.body.ApplyForce(force=(self.direction[0], self.direction[1]), point=self.body.position)

    def changedirection(self):
        self.body.ApplyForce(force=(-self.direction[0], -self.direction[1]), point=self.body.position)
        eins = random.randint(0, 1)
        zwei = random.randint(0, 1)
        newx = 0
        newy = 0
        if eins:
            newx = 8000
        else: 
            newx = 0
            
        if zwei:
            newy = 8000
        else:
            newy = 0
            
        if (not eins and not zwei):
            newx = 8000
            newy = 0
        self.direction = (newx, newy)
        self.body.ApplyForce(force=(self.direction[0], self.direction[1]), point=self.body.position)

class BorderLine:
    body = None
    def __init__(self, world, pos1, pos2, collisions=[], sensor=False):
        """ the positions are expected to be in meters """
        self.world = world
        if BorderLine.body is None:
            BorderLine.body = world.CreateStaticBody(position=(0, 0))
        BorderLine.body.CreateFixture(shape=b2EdgeShape(vertices=[pos1, pos2]), density=1, isSensor=sensor,
                                categoryBits=cats['border'], maskBits=collideWith(collisions))
    
    def destroy(self):
        if self.body is not None:
            self.world.DestroyBody(self.body)
            self.body = None

# TODO create class Bonus
# TODO create class BallBonus(Bonus)
# TODO create class WallBonus(Bonus)
# XXX create class GhostBonus(Bonus)

# XXX create class Turret
# XXX create class TurretBonus(Bonus)
'''
class Pill:
    # TODO refactor as Pill(BallBonus)
    def __init__(self, parentNode, game, world, position, radius=.5):
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor="FFFF00", color='000000')
        d = {'type':'body', 'node':self.node}
        self.world = world
        self.game = game
        self.body = world.CreateDynamicBody(position=position, userData=d)
        self.body.CreateCircleFixture(radius=radius, density=1, friction=1, restitution=1)
        self.body.bullet = True # seriously?
'''
            
class Bat(GameObject):
    # the positions are stored in pixels!
    def __init__(self, renderer, world, parentNode, pos1, pos2):
        GameObject.__init__(self, renderer, world)
        # TODO fix this whole mother...
        self.field = parentNode
        self.pos1 = pos1
        self.pos2 = pos2
        self.width = 5 # set width XXX should depend on bat length
        self.length = self.length() # compute length
        self.ang = self.angle(pos1, pos2) # compute angle
        #self.node = avg.DivNode(parent=parentNode, pos=pos1,size=(self.length,self.width),pivot=(0,0),angle=self.ang,elementoutlinecolor='000FFF')
        self.node = avg.PolygonNode(parent=parentNode)
        d = {'type':'poly', 'node':self.node}
        mid = (pos1 + pos2) / (2 * PPM)
        length = self.length / (2 * PPM)
        wid = self.width / (2 * PPM)
        self.DebugNode = None 
        #avg.WordsNode(parent = self.field, text = "Debug: "+str(self.ang), color = "FFFFFF")
        shapedef = b2PolygonShape(box=(length, wid , (0, 0), self.ang))
        fixturedef = b2FixtureDef(shape=shapedef, density=1, restitution=self.rest(), friction=.3, groupIndex=1)
        self.body = world.CreateKinematicBody(userData=d, position=mid)
        self.body.CreateFixture(fixturedef)
        
        
    # returns the current length of the bat in pixels
    def length(self):
        return math.sqrt((self.pos2[0] - self.pos1[0]) ** 2 + (self.pos2[1] - self.pos2[1]) ** 2)
    
    # computes the restitution of the bat
    def rest(self):
        return 1 # TODO implement dependency on length
    
    # TODO learn basic geometry and come back here
    def angle(self, pos1, pos2):
        vec = pos2 - pos1
        ang = math.atan2(vec.y, vec.x)
        if ang < 0:
            ang += math.pi * 2
        return ang
