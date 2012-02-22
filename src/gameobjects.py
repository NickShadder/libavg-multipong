'''
Created on 15.02.2012

@author: 2526240
'''

import random
import math
from config import PPM, pointsToWin, ballRadius, ghostRadius, brickSize
from libavg import avg, ui
from Box2D import b2EdgeShape, b2PolygonShape, b2FixtureDef, b2CircleShape

cats = {'border':0x0001, 'ghost':0x0002, 'ball':0x0004, 'brick':0x0008}
def dontCollideWith(*categories):
    return reduce(lambda x, y: x ^ y, [cats[el] for el in categories],0xFFFF)

standardXInertia = 20 * ballRadius # XXX solve more elegantly 
g_player = avg.Player.get()

halfBrickSize = brickSize / 2

class Player:
    def __init__(self, game, avgNode):
        self.points = 0
        self.other = None
        self.game = game
        self.zone = avgNode
        avgNode.player = self # monkey patch
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

class GameObject:
    def __init__(self, renderer, world):
        self.renderer = renderer
        self.world = world
        self.renderer.register(self)
    
    def setShadow(self, color):
        # XXX adjust and tweak to look moar better
        shadow = avg.ShadowFXNode()
        shadow.opacity = .7
        shadow.color = color
        shadow.radius = 2
        shadow.offset = (2, 2)
        self.node.setEffect(shadow)
        
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
        self.spawnPoint = parentNode.pivot / PPM # XXX maybe make a static class variable
        self.leftPlayer = leftPlayer
        self.rightPlayer = rightPlayer
        self.lastPlayer = None
        self.diameter = 2 * radius * PPM        
        self.node = avg.ImageNode(parent=parentNode,size=(self.diameter, self.diameter))         
        self.setShadow('FFFF00')
        d = {'type':'body', 'node':self.node, 'obj':self}
        self.body = world.CreateDynamicBody(position=position, userData=d, bullet=True) # XXX reevaluate bullet-ness
        self.body.CreateCircleFixture(radius=radius, density=1, restitution=1,
                                      friction=.01, groupIndex=1, categoryBits=cats['ball'], 
                                      maskBits=dontCollideWith('ghost'), userData='ball')
        self.body.CreateCircleFixture(radius=radius, userData='ball', isSensor=True)
        self.nudge()
        self.node.setEventHandler(avg.CURSORDOWN, avg.TOUCH, lambda e:self.reSpawn()) # XXX remove

    def refreshBitmap(self):
        svg = avg.SVG('../data/img/char/'+('pacman' if self.body.linearVelocity[0]>=0 else 'pacman_left')+'.svg', False)
        self.node.setBitmap(svg.renderElement('layer1',(self.diameter, self.diameter)))

    def reSpawn(self, pos=None):
        # XXX maybe implement a little timeout
        self.lastPlayer = None
        if pos is None:
            pos = self.spawnPoint
        self.body.position = pos
        self.body.active = True # who knows what this ball has been through...
        yOffset = random.randint(-10, 10)
        direction = (-standardXInertia, yOffset) if  self.leftPlayer.points > self.rightPlayer.points else (standardXInertia, yOffset)
        self.nudge(direction)
    
    def zoneOfPlayer(self):
        # XXX I'm sure there is a better way to do this
        lz, rz = self.leftPlayer.zone, self.rightPlayer.zone
        if lz.getAbsPos((0, 0))[0] < self.node.pos[0] < lz.getAbsPos(lz.size)[0]:
            return self.leftPlayer
        elif rz.getAbsPos((0, 0))[0] < self.node.pos[0] < rz.getAbsPos(rz.size)[0]:
            return self.rightPlayer
        else:
            return None
        
    def nudge(self, direction=None):
        self.body.angularVelocity = 0
        self.body.angle = 0
        if direction is None:
            direction = (random.choice([standardXInertia, -standardXInertia]), random.randint(-10, 10)) 
        self.body.linearVelocity = direction
        self.refreshBitmap()

class Ghost(GameObject):
    def __init__(self, renderer, world, parentNode, position, name, mortality=0, radius=ghostRadius):
        GameObject.__init__(self, renderer, world)
        self.parentNode = parentNode
        self.spawnPoint = position
        self.name = name
        self.mortal = mortality
        self.diameter = 2 * radius * PPM
        self.node = avg.ImageNode(parent=parentNode, size=(self.diameter, self.diameter),opacity=.85)
        self.setBitmap()        
        self.setShadow('ADD8E6')
        d = {'type':'body', 'node':self.node, 'obj':self}
        ghostUpper = b2FixtureDef(userData='ghost', shape=b2CircleShape(radius=radius),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'],maskBits=dontCollideWith('ball'))
        ghostLower = b2FixtureDef(userData='ghost', shape=b2PolygonShape(box=(radius, radius / 2, (0, -radius / 2), 0)),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'],maskBits=dontCollideWith('ball'))
        self.body = world.CreateDynamicBody(position=position, fixtures=[ghostUpper, ghostLower],
                                            userData=d, fixedRotation=True) # XXX let them rotate after we fixed their propulsion
        self.move()
        self.changeMortality()
        ui.DragRecognizer(self.node, moveHandler=self.onMove) # XXX just for debugging and fun
    
    def onMove(self, event, offset):
        self.body.position = event.pos / PPM
            
    def flipState(self):
        if self.body.active: # only change if the ghost is currently persistent 
            self.mortal ^= 1
            self.setBitmap()
        
    def setBitmap(self):
        svg = avg.SVG('../data/img/char/' + ('blue' if self.mortal else self.name) + '.svg', False)
        self.node.setBitmap(svg.renderElement('layer1', (self.diameter, self.diameter)))
        self.node.opacity = .85

    def reSpawn(self, pos=None):
        self.body.active = False 
        if pos is None:
            pos = self.spawnPoint
        avg.fadeOut(self.node, 1000, lambda:self.__kill(pos))
    
    def __kill(self, pos):
        self.node.active = False
        g_player.setTimeout(3000, lambda:self.__reAppear(pos)) # XXX adjust timeout or make it configgable 
    
    def __reAppear(self, pos):
        self.body.position = pos
        self.mortal = 0 # ghost respawns in immortal state XXX change this?
        self.setBitmap()
        self.node.active = True
        avg.fadeIn(self.node, 1000, 1, lambda:self.body.__setattr__('active', True))
        
    def move(self, direction=None):
        # TODO implement some kind of AI
        g_player.setTimeout(random.randint(500, 2500), self.move)
        if self.body.active: # just to be sure ;)
            if direction == None:
                direction = random.randint(-10, 10), random.randint(-10, 10)
            self.body.linearVelocity = direction

    def changeMortality(self):
        # TODO implement some kind of AI
        g_player.setTimeout(random.choice([2000, 3000, 4000, 5000, 6000]), self.changeMortality) # XXX store ids for stopping when one player wins
        if self.body.active: # just to be sure ;)
            self.flipState()

class BorderLine:
    body = None
    def __init__(self, world, pos1, pos2, sensor=False, *noCollisions):
        """ the positions are expected to be in meters """
        self.world = world
        if BorderLine.body is None:
            BorderLine.body = world.CreateStaticBody(position=(0, 0))
        BorderLine.body.CreateFixture(shape=b2EdgeShape(vertices=[pos1, pos2]), density=1, isSensor=sensor,
                                categoryBits=cats['border'], maskBits=dontCollideWith(*noCollisions))
    def destroy(self):
        if self.body is not None:
            self.world.DestroyBody(self.body)
            self.body = None

# TODO implement class Bonus
class Bonus:
    pass
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
        self.zone = parentNode
        self.pos1 = pos1
        self.pos2 = pos2
        self.width = 5 # set width XXX should depend on bat length
        self.length = self.length() # compute length
        self.ang = self.angle(pos1, pos2) # compute angle
        #self.node = avg.DivNode(parent=parentNode, pos=pos1,size=(self.length,self.width),pivot=(0,0),angle=self.ang,elementoutlinecolor='000FFF')
        self.node = avg.PolygonNode(parent=parentNode)
        d = {'type':'poly', 'node':self.node, 'obj':self}
        mid = (pos1 + pos2) / (2 * PPM)
        length = self.length / (2 * PPM)
        wid = self.width / (2 * PPM)
        self.DebugNode = None 
        #avg.WordsNode(parent = self.field, text = "Debug: "+str(self.ang), color = "FFFFFF")
        shapedef = b2PolygonShape(box=(length, wid , (0, 0), self.ang))
        fixturedef = b2FixtureDef(userData='bat', shape=shapedef, density=1, restitution=self.rest(), friction=.3, groupIndex=1)
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

#===========================================================================================================================
#  
#===========================================================================================================================

class Brick(Bonus):
    def __init__(self, parentBlock, renderer, world, parentNode, pos):
        GameObject.__init__(self, renderer, world)
        self.parentBlock = parentBlock
        self.node = avg.ImageNode (parent=parentNode, size=(brickSize,brickSize)*PPM,pos=pos)
        self.dragrecognizer = ui.DragRecognizer(self.node, moveHandler=self.onMove) # TODO nach dem einrasten entfernen
    
    # spawn a physical object
    def materialze(self,pos=None):
        if pos==None:
            pos = (self.node.pos+self.node.pivot)/PPM # TODO this looks like trouble
        data = {'type':'body', 'node':self.node, 'obj':self}
        fixtureDef = b2FixtureDef (userData='ghost', shape=b2PolygonShape (box=(brickSize / 2, brickSize / 2)),
                                  density=1, friction=.1, restitution=1, groupIndex=1, categoryBits=cats['brick'])
        self.body = self.world.CreateKinematicBody(position=pos, fixture=fixtureDef,
                                            userData=data)
    
#=======================================================================================================================
# TODO solve better!
#=======================================================================================================================
    def onMove(self, event, offset):
        self.parentBlock.move(event, offset)
        #self.body.position = event.pos / PPM                is called in block!
        
    # is called, when the ball or bullet hits the brick
    def hit(self):
        pass
        # todo there should be more than this here


class DiamondBrick(Brick):
    def __init__(self, parentBlock, renderer, world, parentNode, x, y):
        Brick.__init__(self, parentBlock, renderer, world, parentNode, x, y)
        #svg = avg.SVG('../data/img/?/?.svg', False)                                             #TODO: image
        #self.node.setBitmap(svg.renderElement('layer1', (brickSize * PPM, brickSize * PPM)))


#TODO: other brickTypes

#===========================================================================================================================
# TODO The block should stop existing after its bricks have been placed! It should only be a container for the bricks while they are being put into place. 
#===========================================================================================================================

# appears as building material - consists of bricks - !Superclass! there are several types of Blocks
# brickList contains the bricks which were not hit so far
class Block:
    def __init__(self, parentNode):
        self.parentNode = parentNode
        self.brickList = []
        self.node = None                #TODO: create an appropriate Node to handle drag-event at this place
    
    def move(self, event, offset):
        pass
        #self.brick0.pos = (event.x - offset[0], event.y - offset[1])


#===========================================================================================================================
# TODO Get rid of the following copy pasta! use lists of bricks instead!!!
#===========================================================================================================================

# this Block consists only of one brick
class SingleBlock (Block):
    def __init__(self, parentNode, position, renderer, world, type):
        Block.__init__(self, parentNode)
        #depending on the respective type create the appropriate brick
        # the calls of Brick-constructor have to be changed and the choice of the right brick-type has to be done        
        self.brick0 = Brick(self.node, x - halfBrickSize, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        
# this Block consists of two bricks
class DoubleBlock (Block):
    def __init__(self, parentNode, position, renderer, world, type):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x - halfBrickSize, y - brickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x - halfBrickSize, y, colour, self)
        self.brickList.append(self.brick1)
        
# this Block consists of four bricks which form an rectangle
class RectBlock (Block):
    def __init__(self, parentNode, position, renderer, world, type):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - brickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - brickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x - brickSize, y, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x, y, colour, self)
        self.brickList.append(self.brick3)
             
# this Block consists of four bricks which are arranged in a line
class LineBlock (Block):
    def __init__(self, parentNode, position, renderer, world, type):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x - halfBrickSize, y - 2 * brickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x - halfBrickSize, y - brickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x - halfBrickSize, y, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x - halfBrickSize, y + brickSize, colour, self)
        self.brickList.append(self.brick3)
        
        
#this Block consists of four bricks which are arranged like a L (left)
class LBlockLeft (Block):
    def __init__(self, parentNode, position, renderer, world, type):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x - brickSize, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick3)


#this Block consists of four bricks which are arranged like a L (right - mirror inverted)
class LBlockRight (Block):
    def __init__(self, parentNode, position, renderer, world, type):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick3)


#this Block consists of four bricks which are arranged like an uppercase gamma (left)
class GammaBlockLeft (Block):
    def __init__(self, parentNode, position, renderer, world, type):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x - brickSize, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick3)


#this Block consists of four bricks which are arranged like an uppercase gamma (right - mirror inverted)
class GammaBlockRight (Block):
    def __init__(self, parentNode, position, renderer, world, type):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick3)


# this Block consists of three bricks which are arranged in a line, in the middle a fourth brick is added (left)
class MiddleBlockLeft (Block):
    def __init__(self, parentNode, position, renderer, world, type):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x - brickSize, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick3)


# this Block consists of three bricks which are arranged in a line, in the middle a fourth brick is added (right - mirror inverted)
class MiddleBlockRight (Block):
    def __init__(self, parentNode, position, renderer, world, type):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x - brickSize, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick3)
