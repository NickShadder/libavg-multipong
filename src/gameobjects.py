'''
Created on 15.02.2012

@author: 2526240
'''

import random
import math
from config import PPM
from libavg import avg
from Box2D import b2EdgeShape, b2PolygonShape, b2FixtureDef

class Ball(object):
    # TODO refactor with respect to the new rendering mechanism
    def __init__(self, parentNode, game, world, position, radius=.5):
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor="FFFF00", color='000000')
        d = {'type':'body', 'node':self.node}
        self.world = world
        self.game = game
        self.body = world.CreateDynamicBody(position=position, userData=d)
        self.body.CreateCircleFixture(radius=radius, density=1, friction=0, restitution=1,groupIndex=1,maskBits=0x0002)
      
    def destroy(self):
        if self.body is not None:
            self.world.DestroyBody(self.body)
            self.body = None
        if self.node is not None:
            self.node.active = False
            self.node.unlink()
            self.node = None
    
    # TODO should return the last player who touched it
    def lastPlayer(self):
        pass
    
    # TODO should return the player to whom the current zone the ball is in belongs, or None if the ball is in the middle
    def zone(self):
        pass
    
    # TODO implement some intelligent bahviour here 
    # e.g. the ball flies towards the winning player
    def start_moving(self, startpos):
        if random.choice([True, False]):
            self.body.ApplyForce(force=(5000, random.randint(-2000, 2000)), point=startpos)
        else:
            self.body.ApplyForce(force=(-5000, random.randint(-2000, 2000)), point=startpos)
        
class Player(object):
    def __init__(self):
        self.__points = 0
        # TODO make the points an internal wordsnode
        # TODO keep a reference to the game
    
    def addPoint(self):
        self.__points += 1
        # TODO this should also update the text and check whether we have a winner
    
    # TODO this method shouldn't be needed
    def getPoints(self):
        return self.__points
    
    # TODO should return the other player
    def other(self):
        pass
    
class Ghost(object):
    def __init__(self, parentNode, world, position, color,mortality=0, radius=.5):
        # TODO create a realistic body form for the ghosts using b2LoopShape and b2CircleShape
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor=color, color='000000')
        self.node.setEventHandler(avg.CURSORDOWN,avg.TOUCH | avg.MOUSE,self.antouch)
        self.mortal = 0
        self.old_color = color
        self.direction = (8000, 10)
        self.position = position
        self.world = world
        d = {'type':'body', 'node':self.node}
        self.body = world.CreateDynamicBody(position=position, userData=d)        
        self.body.CreateCircleFixture(radius=radius, density=1, friction=1,groupIndex=-1)
        self.body.ApplyForce(force=(self.direction[0], self.direction[1]), point=self.position)
            
    def antouch(self,event): 
        
        self.body.position=(random.randint(10, 60), random.randint(10, 40))         
            
    def setDir(self, s):
        self.body.ApplyForce(force=((-1) * self.direction[0], (-1) * self.direction[1]), point=self.position)
        if s == "left":
            self.direction = (8000, self.direction[1])   
        else:
            self.direction = (-8000, self.direction[1])
        self.body.ApplyForce(force=(self.direction[0], self.direction[1]), point=self.position)
        
    def destroy(self):
        if self.body is not None:
            self.world.DestroyBody(self.body)
            self.body = None
        if self.node is not None:
            self.node.active = False
            self.node.unlink()
            self.node = None
            
    def changedirection(self):
        self.body.ApplyForce(force=(-self.direction[0], -self.direction[1]), point=self.position)
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
        self.body.ApplyForce(force=(self.direction[0], self.direction[1]), point=self.position)

class GhostLine:
    # TODO refactor this class: make it configgable and use it also for upper and lower borders
    def __init__(self, avg_parentNode, world, pos1, pos2):
        self.node = avg.LineNode(parent=avg_parentNode, color='000000') # for debugging only
        self.world = world
        d = {'type':'line', 'node':self.node}
        self.body = world.CreateStaticBody(userData=d, shapes=b2EdgeShape(vertices=[pos1, pos2]), position=(1, 0),categoryBits=0x0002)
    
    def destroy(self):
        if self.body is not None:
            self.world.DestroyBody(self.body)
            self.body = None
        if self.node is not None:
            self.node.active = False
            self.node.unlink()
            self.node = None
            

# TODO create class Bonus
# TODO create class BallBonus(Bonus)
# TODO create class WallBonus(Bonus)
# XXX create class GhostBonus(Bonus)

# XXX create class Turret
# XXX create class TurretBonus(Bonus)

class Pill(object):
    # TODO refactor as Pill(BallBonus)
    def __init__(self, parentNode, game, world, position, radius=.5):
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor="FFFF00", color='000000')
        d = {'type':'body', 'node':self.node}
        self.world = world
        self.game = game
        self.body = world.CreateDynamicBody(position=position, userData=d)
        self.body.CreateCircleFixture(radius=radius, density=1, friction=1, restitution=1)
        self.body.bullet = True # seriously?
       
class Bat:
    # the positions are stored in pixels!
    def __init__(self, parentNode, world, pos1, pos2):
        # TODO fix this whole mother...
        self.world = world
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
        len = self.length / (2 * PPM)
        wid = self.width / (2 * PPM)
        self.DebugNode = None 
        #avg.WordsNode(parent = self.field, text = "Debug: "+str(self.ang), color = "FFFFFF")
        shapedef = b2PolygonShape(box=(len,wid , (0, 0), self.ang))
        fixturedef = b2FixtureDef(shape=shapedef, density=1, restitution=self.rest(), friction=.3,groupIndex=1)
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
    
    def destroy(self):
        if self.body is not None:
            self.world.DestroyBody(self.body)
            self.body = None
        if self.node is not None:
            self.node.active = False
            self.node.unlink()
            self.node = None