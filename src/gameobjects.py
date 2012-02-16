'''
Created on 15.02.2012

@author: 2526240
'''

from libavg import avg
import random
from Box2D import b2EdgeShape
import math

class Ball(object):
    def __init__(self, parentNode, world, position, radius=.5):
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor="FFFF00",color='000000')
        d = {'type':'circle', 'node':self.node}
        self.circle = world.CreateDynamicBody(position=position, userData=d)
        self.circle.CreateCircleFixture(radius=radius, density=1, friction=1,restitution=1)
        self.circle.bullet = True;
        
    def destroy(self):
        self.world.DestroyBody(self.circle)
        self.node.active = False
        self.node = None
        self.circle = None
    
    def start_moving(self,startpos):
        x = random.randint(0,1)
        if x:
            self.circle.ApplyForce(force=(5000,-2000), point=startpos)
        else:
            self.circle.ApplyForce(force=(-5000,2000), point=startpos)
        
#    def getX(self):
#        pass self.circle.position[0]
#    
#    def getY(self): 
#        pass self.circle.position[1]
#    
class Ghost(object):
    def __init__(self, parentNode, world, position,color, radius=.5):
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor=color,color='000000')
        self.direction = (3000,10)
        self.position = position
        self.world = world
        d = {'type':'circle', 'node':self.node}
        self.circle = world.CreateDynamicBody(position=position, userData=d)
        self.circle.CreateCircleFixture(radius=radius, density=1, friction=1,restitution=0)
        self.circle.bullet = True;
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

class Bat:
    def __init__(self, avg_parentNode, world, pos1, pos2):
        self.node = avg.LineNode(parent=avg_parentNode, color='000FFF')
        d = {'type':'line', 'node':self.node}
        self.body = world.CreateStaticBody(userData=d, shapes=b2EdgeShape(vertices=[pos1, pos2]), position=(1, 0))
    
    # returns the current length of the bat 
    def length(self):
        pos1 = self.body.fixtures[0].shape.vertices[0]
        pos2 = self.body.fixtures[0].shape.vertices[1]
        return math.sqrt((pos2.x - pos1.x) ** 2 + (pos2.y - pos2.y) ** 2)
    
    # computes the restitution of the bat
    def rest(self):
        return 1 # TODO implement dependency on length
    
    def destroy(self):
        self.world.DestroyBody(self.body)
        self.node.active = False
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
