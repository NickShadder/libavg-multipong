'''
Created on 15.02.2012

@author: 2526240
'''

import random
import math
from config import PPM
from libavg import avg
from Box2D import b2EdgeShape,b2PolygonShape,b2FixtureDef

class Ball(object):
    def __init__(self, parentNode, game, world, position, radius=.5):
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor="FFFF00",color='000000')
        self.node.setEventHandler(avg.CURSORDOWN,avg.TOUCH | avg.MOUSE,self.antouch)
        d = {'type':'circle', 'node':self.node}
        self.world = world
        
        self.game = game
        self.circle = world.CreateDynamicBody(position=position, userData=d)
        self.circle.CreateCircleFixture(radius=radius, density=1, friction=1,restitution=1,maskBits=0x0004)
        self.circle.bullet = True;
      
    def antouch(self,event):
        self.game.newBall();        
      
    def destroy(self):
        self.world.DestroyBody(self.circle)
        self.node.active = False
        self.node.unlink()
        self.node = None
        self.circle = None
    
    def start_moving(self,startpos):
        x = random.randint(0,1)
        #self.circle.ApplyForce(force=(0,1000), point=startpos)
        if x:
            self.circle.ApplyForce(force=(4000,random.randint(-1000,1000)), point=startpos)
        else:
            self.circle.ApplyForce(force=(-4000,random.randint(-1000,1000)), point=startpos)
        
        
        
#    def getX(self):
#        pass self.circle.position[0]
#    
#    def getY(self): 
#        pass self.circle.position[1]
#    

class Player(object):
    def __init__(self):
        self.__points = 0
    
    def addPoint(self):
        self.__points += 1
    
    def getPoints(self):
        return self.__points
    

class Ghost(object):
    def __init__(self, parentNode, world, position,color, radius=.5):
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor=color,color='000000')
        self.direction = (3000,10)
        self.position = position
        self.world = world
        d = {'type':'circle', 'node':self.node}
        self.circle = world.CreateDynamicBody(position=position, userData=d)
        
        self.circle.CreateCircleFixture(radius=radius, density=1, friction=1,restitution=0,groupIndex = -1)
        #self.circle.fixtures[0].groupIndex = -8
        
        self.circle.bullet = True;
        self.circle.ApplyForce(force=(self.direction[0],self.direction[1]), point=self.position)
        
        
    def setDir(self,s):
        self.circle.ApplyForce(force=((-1)*self.direction[0],(-1)*self.direction[1]), point=self.position)
        if s == "left":
            self.direction = (3000,self.direction[1])   
        else:
            self.direction = (-3000,self.direction[1])
        self.circle.ApplyForce(force=(self.direction[0],self.direction[1]), point=self.position)
        
    def destroy(self):
        self.world.DestroyBody(self.circle)
        self.node.active = False
        self.node = None
        self.circle = None
            
    def changedirection(self):
        self.circle.ApplyForce(force=(-self.direction[0],-self.direction[1]), point=self.position)
        eins = random.randint(0,1)
        zwei = random.randint(0,1)
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
        self.direction = (newx,newy)
        self.circle.ApplyForce(force=(self.direction[0],self.direction[1]), point=self.position)

class Line:
    def __init__(self, avg_parentNode, world, pos1, pos2):
        self.node = avg.LineNode(parent=avg_parentNode, color='000FFF')
        self.world = world
        d = {'type':'line', 'node':self.node}
        self.body = world.CreateStaticBody(userData=d, shapes=b2EdgeShape(vertices=[pos1, pos2]), position=(1, 0), maskBits=0x0004)
    
    def destroy(self):
        self.world.DestroyBody(self.body)
        self.node.active = False
        self.node = None


class Pill(object):
    def __init__(self, parentNode, game, world, position, radius=.5):
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor="FFFF00",color='000000')
        d = {'type':'circle', 'node':self.node}
        self.world = world
        self.game = game
        self.circle = world.CreateDynamicBody(position=position, userData=d)
        self.circle.CreateCircleFixture(radius=radius, density=1, friction=1,restitution=1,maskBits=0x0004)
        self.circle.bullet = True;
       

class Bat:
    # the positions are in pixels!
    def __init__(self, field, world, pos1, pos2):
        self.world = world
        self.field = field
        self.pos1 = pos1
        self.pos2 = pos2
        self.width = 5 # set width
        self.length =  self.length() # compute length
        self.ang = self.angle(pos1, pos2) # compute angle
        #self.node = avg.DivNode(parent=field, pos=pos1,size=(self.length,self.width),pivot=(0,0),angle=self.ang,elementoutlinecolor='000FFF')
        self.node = avg.PolygonNode(parent=field)
        d = {'type':'poly', 'node':self.node}
        mid = (pos1+pos2)/(2*PPM)
        shapedef = b2PolygonShape(box=(self.length/(2*PPM), self.width/(2*PPM), (0,0), self.ang))
        fixturedef = b2FixtureDef(shape=shapedef,density=1,restitution=self.rest(),friction=.3)
        self.body = world.CreateKinematicBody(userData=d, position=mid)
        self.body.CreateFixture(fixturedef)
        
    # returns the current length of the bat in pixels
    def length(self):
        return math.sqrt((self.pos2[0] - self.pos1[0]) ** 2 + (self.pos2[1] - self.pos2[1]) ** 2)
    
    # computes the restitution of the bat
    def rest(self):
        return 1 # TODO implement dependency on length
    
    def angle(self,pos1,pos2):
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
