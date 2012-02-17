'''
Created on 15.02.2012

@author: 2526240
'''

import random
import math
from config import PPM,DebugNode
from libavg import avg
from Box2D import b2EdgeShape, b2PolygonShape, b2FixtureDef

class Ball(object):
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
    
    def start_moving(self, startpos):
        if random.choice([True, False]):
            self.body.ApplyForce(force=(4000, random.randint(-1000, 1000)), point=startpos)
        else:
            self.body.ApplyForce(force=(-4000, random.randint(-1000, 1000)), point=startpos)
        
class Player(object):
    def __init__(self):
        self.__points = 0
    
    def addPoint(self):
        self.__points += 1
    
    def getPoints(self):
        return self.__points
    
class Ghost(object):
    def __init__(self, parentNode, world, position, color,mortality=0, radius=.5):
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor=color, color='000000')
        self.node.setEventHandler(avg.CURSORDOWN,avg.TOUCH | avg.MOUSE,self.antouch)
        self.mortal = 0
        self.old_color = color
        self.direction = (3000, 10)
        self.position = position
        self.world = world
        d = {'type':'body', 'node':self.node}
        self.body = world.CreateDynamicBody(position=position, userData=d)        
        self.body.CreateCircleFixture(radius=radius, density=1, friction=1,groupIndex=-1)
        self.body.ApplyForce(force=(self.direction[0], self.direction[1]), point=self.position)
            
    def antouch(self,event): 
        self.body.ApplyForce(force=(-self.direction[0], -self.direction[1]), point=self.position) 
        self.direction = (0, 0)            
            
    def setDir(self, s):
        self.body.ApplyForce(force=((-1) * self.direction[0], (-1) * self.direction[1]), point=self.position)
        if s == "left":
            self.direction = (3000, self.direction[1])   
        else:
            self.direction = (-3000, self.direction[1])
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
            newx = 3000
        else: 
            newx = 0
            
        if zwei:
            newy = 3000
        else:
            newy = 0
            
        if (not eins and not zwei):
            newx = 3000
            newy = 0
        self.direction = (newx, newy)
        self.body.ApplyForce(force=(self.direction[0], self.direction[1]), point=self.position)

class GhostLine:
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

class Pill(object):
    def __init__(self, parentNode, game, world, position, radius=.5):
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor="FFFF00", color='000000')
        d = {'type':'body', 'node':self.node}
        self.world = world
        self.game = game
        self.body = world.CreateDynamicBody(position=position, userData=d)
        self.body.CreateCircleFixture(radius=radius, density=1, friction=1, restitution=1)
        self.body.bullet = True;
       
class Bat:
    # the positions are stored in pixels!
    def __init__(self, parentNode, world, pos1, pos2):
        self.world = world
        self.field = parentNode
        self.pos1 = pos1
        self.pos2 = pos2
        self.width = 5 # set width
        self.length = self.length() # compute length
        self.ang = self.angle(pos1, pos2) # compute angle
        #self.node = avg.DivNode(parent=parentNode, pos=pos1,size=(self.length,self.width),pivot=(0,0),angle=self.ang,elementoutlinecolor='000FFF')
        self.node = avg.PolygonNode(parent=parentNode)
        d = {'type':'poly', 'node':self.node}
        mid = (pos1 + pos2) / (2 * PPM)
        len = self.length / (2 * PPM)
        wid = self.width / (2 * PPM)
        self.DebugNode = avg.WordsNode(parent = self.field, text = "Debug: "+str(self.ang), color = "FFFFFF")
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
        if self.DebugNode is not None:
            self.DebugNode.active = False
            self.DebugNode.unlink()
            self.DebugNode = None
        
'''
class Bat:
    def __init__(self,world,pos1,pos2,avg_parentNode):  
        width = 5 # set width
        length =  math.sqrt((pos2.x-pos1.x)**2+(pos2.y-pos2.y)**2) # compute length
        ang = self.angle(pos1, pos2) # compute angle
        mid = (pos1+pos2)/2 # compute middle
        
        if config.debug:
            print 'length:',length
        if config.debug:
            print 'ang: ',ang      
        if config.debug:
            print 'mid: ',mid
            
        self.node = avg.PolygonNode(parent=avg_parentNode)
        #self.node2 = avg.RectNode(parent=avg_parentNode,size=(length,width),pos=(mid[0]-length,mid[1]),angle=ang,fillcolor='FF1337',fillopacity=1)
        d = {'type':'poly','node':self.node}        
        mid /= PPM # scale from pixels to meters
        length /= 2*PPM
        width /= 2*PPM
        
        self.body = world.CreateStaticBody(position=mid,userData=d,shapes=b2PolygonShape(box=(width/(2*PPM),length/(2*PPM),mid,ang)))
        
        print self.body.fixtures[0].shape.vertices
        
    def angle(self,pos1,pos2):
        vec = pos2 - pos1
        ang = math.atan2(vec.y, vec.x)
        if ang < 0:
            ang += math.pi * 2
        return ang
    
    def destroy(self):
        self.world.DestroyBody(self.body)
        self.node.active = False
        self.node = None
'''
