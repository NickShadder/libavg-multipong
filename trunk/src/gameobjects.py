'''
Created on 15.02.2012

@author: 2526240
'''

import random
import math
from config import PPM
from libavg import avg,ui
from Box2D import b2EdgeShape, b2PolygonShape, b2FixtureDef, b2CircleShape

cats = {'border':0x0001, 'ghost':0x0002, 'ball':0x0004, 'brick':0x0008}
def collideWith(categories):
    return reduce(lambda x,y: x|y, [cats[el] for el in categories], 0x0000)

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
    # TODO refactor with respect to the new rendering mechanism
    def __init__(self, renderer, world, parentNode, position, radius=1):
        GameObject.__init__(self, renderer, world)
        diameter = 2 * radius * PPM
        svg = avg.SVG('../data/img/pacman.svg', False)
        self.node = svg.createImageNode('layer1', dict(parent=parentNode), (diameter, diameter))
        d = {'type':'body', 'node':self.node}
        self.body = world.CreateDynamicBody(position=position, userData=d)
        self.body.CreateCircleFixture(radius=radius, density=1, restitution=1, categoryBits=cats['ball'])
        self.lastPlayer = None

    
    # TODO should return the player to whom the current zone the ball is in belongs, or None if the ball is in the middle
    def zone(self):
        pass
    
    # TODO implement some intelligent bahviour here 
    # e.g. the ball flies towards the winning player or something using lastPlayer 
    def start_moving(self, startpos):
        if random.choice([True, False]):
            self.body.ApplyForce(force=(5000, random.randint(-2000, 2000)), point=startpos)
        else:
            self.body.ApplyForce(force=(-5000, random.randint(-2000, 2000)), point=startpos)
        
class Player:
    def __init__(self, avgNode):
        self.points = 0
        self.other = None
        self.zone = avgNode
        # TODO make the points an internal wordsnode
        # TODO keep a reference to the game
    
    def addPoint(self, points=1):
        self.points += points
        # TODO this should also update the text and check whether we have a winner

    def removePoint(self, points=1):
        self.points -= points
        if self.points < 0:
            self.points = 0
    
    # TODO should return the other player
    def other(self):
        pass

class Ghost(GameObject):
    def __init__(self, renderer, world, parentNode, position, name, mortality=0, radius=2):
        GameObject.__init__(self, renderer, world)
        self.parentNode = parentNode
        self.name = name
        self.mortal = mortality                
        self.diameter = 2 * radius * PPM                
        self.node = avg.ImageNode(parent=parentNode, size=(self.diameter, self.diameter))
        self.setBitmap(name)
        d = {'type':'body', 'node':self.node}
        ghostUpper = b2FixtureDef(shape=b2CircleShape(radius=radius),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'])
        ghostLower = b2FixtureDef(shape=b2PolygonShape(box=(radius, radius / 2, (0, -radius / 2), 0)),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'])
        self.body = world.CreateDynamicBody(position=position, fixtures=[ghostUpper, ghostLower],
                                            userData=d, fixedRotation=True) # XXX let them rotate after we fixed their propulsion
        ui.DragRecognizer(self.node, moveHandler=self.onMove) # just for debugging and fun
        
        # XXX I don't like this...        
        self.direction = (8000, 10) # XXX what is this?!
        self.body.ApplyForce(force=(self.direction[0], self.direction[1]), point=self.body.position)
    
    def onMove(self, event, offset):
        self.body.position=(event.pos)/PPM
            
    def flipState(self):
        self.setBitmap(self.name if self.mortal else 'blue')
        self.mortal ^= 1
        
    def setBitmap(self, name):
        svg = avg.SVG('../data/img/' + name + '.svg', False)        
        self.node.setBitmap(svg.renderElement('layer1', (self.diameter, self.diameter)))        
            
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
        len = self.length / (2 * PPM)
        wid = self.width / (2 * PPM)
        self.DebugNode = None 
        #avg.WordsNode(parent = self.field, text = "Debug: "+str(self.ang), color = "FFFFFF")
        shapedef = b2PolygonShape(box=(len, wid , (0, 0), self.ang))
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
