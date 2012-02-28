'''
Created on 15.02.2012

@author: 2526240
'''

import random
import math
from config import PPM, pointsToWin, ballRadius, ghostRadius, brickSize, maxBatSize
from libavg import avg, ui
from Box2D import b2EdgeShape, b2PolygonShape, b2FixtureDef, b2CircleShape

cats = {'border':0x0001, 'ghost':0x0002, 'ball':0x0004, 'brick':0x0008}
def dontCollideWith(*categories):
    return reduce(lambda x, y: x ^ y, [cats[el] for el in categories], 0xFFFF)

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
        self.renderer, self.world = renderer, world
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
        svg = avg.SVG('../data/img/char/pacman.svg', False)
        self.node = svg.createImageNode('layer1', dict(parent=parentNode), (self.diameter, self.diameter))
        self.setShadow('FFFF00')
        self.body = world.CreateDynamicBody(position=position, userData=self, active=False, bullet=True) # XXX reevaluate bullet-ness
        self.body.CreateCircleFixture(radius=radius, density=1, restitution=1, # XXX remove this
                                      friction=.01, groupIndex=1, categoryBits=cats['ball'],
                                      maskBits=dontCollideWith('ghost'), userData='ball')
        self.body.CreateCircleFixture(radius=radius, userData='ball', isSensor=True)
        self.__appear(lambda:self.nudge())
        self.node.setEventHandler(avg.CURSORDOWN, avg.TOUCH, lambda e:self.reSpawn()) # XXX remove

    def render(self):
        pos = self.body.position * PPM - self.node.size / 2
        self.node.pos = (pos[0], pos[1])
        angle = self.body.angle + math.pi if self.body.linearVelocity[0] < 0 else self.body.angle
        self.node.angle = angle

    def reSpawn(self, pos=None):
        self.body.active = False
        self.lastPlayer = None
        if pos is None:
            pos = self.spawnPoint
        self.body.position = pos
        yOffset = random.randint(-10, 10)
        direction = (-standardXInertia, yOffset) if  self.leftPlayer.points > self.rightPlayer.points else (standardXInertia, yOffset)
        self.__appear(lambda:self.nudge(direction))
        
    def __appear(self,stopAction=None):
        wAnim = avg.LinearAnim(self.node,'width',300,1,int(self.node.width))
        hAnim = avg.LinearAnim(self.node,'height',300,1,int(self.node.height))
        avg.ParallelAnim([wAnim,hAnim],None,stopAction,300).start()
    
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
        self.body.active = True
        self.body.angularVelocity = 0
        self.body.angle = 0
        if direction is None:
            direction = (random.choice([standardXInertia, -standardXInertia]), random.randint(-10, 10)) 
        self.body.linearVelocity = direction
        self.render()

class Ghost(GameObject):
    d = 2 * ghostRadius * PPM
    blue = avg.SVG('../data/img/char/blue.svg', False).renderElement('layer1', (d, d))
    def __init__(self, renderer, world, parentNode, position, name, mortality=1, radius=ghostRadius): # make somehow uniform e.g. by prohibiting other ghost radii
        GameObject.__init__(self, renderer, world)
        self.parentNode = parentNode
        self.spawnPoint = position
        self.name = name
        self.mortal = mortality
        self.diameter = 2 * radius * PPM
        self.colored = avg.SVG('../data/img/char/' + name + '.svg', False).renderElement('layer1', (self.diameter, self.diameter))
        self.node = avg.ImageNode(parent=parentNode, opacity=.85)
        self.setShadow('ADD8E6')
        ghostUpper = b2FixtureDef(userData='ghost', shape=b2CircleShape(radius=radius),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'], maskBits=dontCollideWith('ball'))
        ghostLower = b2FixtureDef(userData='ghost', shape=b2PolygonShape(box=(radius, radius / 2, (0, -radius / 2), 0)),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'], maskBits=dontCollideWith('ball'))
        self.body = world.CreateDynamicBody(position=position, fixtures=[ghostUpper, ghostLower],
                                            userData=self, fixedRotation=True)
        self.changeMortality()
        self.render()
        self.move()
        ui.DragRecognizer(self.node, moveHandler=self.onMove) # XXX just for debugging and fun
    
    def onMove(self, event, offset):
        self.body.position = event.pos / PPM
            
    def flipState(self):
        if self.body.active: # only flip if the ghost is currently persistent
            self.mortal ^= 1
            self.node.setBitmap(self.blue if self.mortal else self.colored)
        
    def render(self):
        pos = self.body.position * PPM - self.node.size / 2
        self.node.pos = (pos[0], pos[1])
        self.node.angle = self.body.angle
        
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
        self.mortal = 0 # ghost respawns in immortal state XXX rerender this?
        self.render()
        self.node.active = True
        avg.fadeIn(self.node, 1000, .85, lambda:self.body.__setattr__('active', True))
        
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
        # XXX add restitution, but beware of bouncing ghosts
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
#    XXX find out why this optimization makes the bat appear slightly above the intended position for a very short time (a single frame?)  
#    batImgLen = maxBatSize * PPM / 2
#    if batImgLen < 1: batImgLen = 1
#    batImgWidth = batImgLen / 10 
#    if batImgWidth < 1: batImgWidth = 1
#    blueBat = avg.SVG('../data/img/char/bat_blue.svg', False).renderElement('layer1', (batImgWidth,batImgLen))
#    greenBat = avg.SVG('../data/img/char/bat_green.svg', False).renderElement('layer1', (batImgWidth,batImgLen))
    def __init__(self, renderer, world, parentNode, pos):
        GameObject.__init__(self, renderer, world)
        self.zone = parentNode
        vec = pos[1] - pos[0]
        self.length = vec.getNorm()
        if self.length < 1: self.length = 1
        width = (maxBatSize * PPM - self.length) / 10
        if width < 1: width = 1
        angle = math.atan2(vec.y, vec.x)
#        self.node = avg.ImageNode(parent=parentNode)
#        self.node.setBitmap(Bat.blueBat if parentNode.pos==(0,0)else Bat.greenBat)
        self.svg = avg.SVG('../data/img/char/' + ('bat_blue'if parentNode.pos == (0, 0)else'bat_green') + '.svg', False)
        self.node = self.svg.createImageNode('layer1', dict(parent=parentNode), (width, self.length))
        mid = (pos[0] + pos[1]) / (2 * PPM)
        width = width / (2 * PPM)
        length = self.length / (2 * PPM)
        shapedef = b2PolygonShape(box=(length, width))
        fixturedef = b2FixtureDef(userData='bat', shape=shapedef, density=1, restitution=1, friction=.02, groupIndex=1)
        self.body = world.CreateKinematicBody(userData=self, position=mid, angle=angle)
        self.body.CreateFixture(fixturedef)
        self.render()
        
    def render(self):
        pos = self.body.position * PPM - self.node.size / 2
        self.node.pos = self.zone.getRelPos((pos[0], pos[1]))
        self.node.angle = self.body.angle - math.pi / 2
        ver = self.body.fixtures[0].shape.vertices
        h = (ver[1][0] - ver[0][0])
        w = (ver[-1][1] - ver[0][1])
        self.node.size = avg.Point2D(w, h) * PPM
    
      
#===========================================================================================================================
#  
#===========================================================================================================================

class Brick(Bonus):
    def __init__(self, parentBlock, renderer, world, parentNode, pos):
        GameObject.__init__(self, renderer, world)
        self.parentBlock = parentBlock
        self.node = avg.ImageNode (parent=parentNode, size=(brickSize, brickSize) * PPM, pos=pos)
        self.dragrecognizer = ui.DragRecognizer(self.node, moveHandler=self.onMove) # TODO nach dem einrasten entfernen, gehoert hier nicht her --> Block
    
    # spawn a physical object
    def materialze(self, pos=None):
        if pos == None:
            pos = (self.node.pos + self.node.pivot) / PPM # TODO this looks like trouble
        data = {'type':'body', 'node':self.node, 'obj':self}
        fixtureDef = b2FixtureDef (userData='ghost', shape=b2PolygonShape (box=(brickSize / 2, brickSize / 2)),
                                  density=1, friction=.1, restitution=1, groupIndex=1, categoryBits=cats['brick'])
        self.body = self.world.CreateKinematicBody(position=pos, fixture=fixtureDef,
                                            userData=data)
    
    def changeRelPos (self, x, y):
        self.node.pos = (self.node.pos[0] + x, self.node.pos[1] + y)
    
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
    def __init__(self, parentBlock, renderer, world, parentNode, position):
        Brick.__init__(self, parentBlock, renderer, world, parentNode, position)
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
# TODO /
#===========================================================================================================================

# this Block consists only of one brick
class SingleBlock (Block):
    def __init__(self, parentNode, position, renderer, world, brick):
        Block.__init__(self, parentNode)
        self.brickList.append(brick)

class DiamondSingleBlock (SingleBlock):
    def __init__(self, parentNode, position, renderer, world):
        SingleBlock.__init__(self, parentNode, position, renderer, world, DiamondBrick(self, renderer, world, parentNode, (position[0] - halfBrickSize, position[1] - halfBrickSize)))

        
# this Block consists of two bricks
class DoubleBlock (SingleBlock):
    def __init__(self, parentNode, position, renderer, world, brick):
        SingleBlock.__init__(self, parentNode, position, renderer, world, brick)
        brick1 = copy.deepcopy(brick)
        brick1.changeRelPos(0, brickSize)

class DiamondDoubleBlock (DoubleBlock):
    def __init__(self, parentNode, position, renderer, world):
        DoubleBlock.__init__(self, parentNode, position, renderer, world, DiamondBrick(self, renderer, world, parentNode, (position[0] - halfBrickSize, position[1] - brickSize)))

 
 #
 #    Remains to be done like above
 #
        
# this Block consists of four bricks which form an rectangle
class RectBlock (DoubleBlock):
    def __init__(self, parentNode, position, renderer, world, brick):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - brickSize, colour, self)
        self.brickList.append(self.brick0)
        #self.brick1 = Brick(self.parentNode, x, y - brickSize, colour, self)
        #self.brick2 = Brick(self.parentNode, x - brickSize, y, colour, self)
        #self.brick3 = Brick(self.parentNode, x, y, colour, self)
             
# this Block consists of four bricks which are arranged in a line
class LineBlock (Block):
    def __init__(self, parentNode, position, renderer, world, brick):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x - halfBrickSize, y - 2 * brickSize, colour, self)
        self.brickList.append(self.brick0)
        #self.brick1 = Brick(self.parentNode, x - halfBrickSize, y - brickSize, colour, self)
        #self.brick2 = Brick(self.parentNode, x - halfBrickSize, y, colour, self)
        #self.brick3 = Brick(self.parentNode, x - halfBrickSize, y + brickSize, colour, self)
        
        
#this Block consists of four bricks which are arranged like a L (left)
class LBlockLeft (Block):
    def __init__(self, parentNode, position, renderer, world, brick):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        #self.brick1 = Brick(self.parentNode, x - brickSize, y - halfBrickSize, colour, self)
        #self.brick2 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)
        #self.brick3 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)



#this Block consists of four bricks which are arranged like a L (right - mirror inverted)
class LBlockRight (Block):
    def __init__(self, parentNode, position, renderer, world, brick):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        #self.brick1 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)
        #self.brick2 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)
        #self.brick3 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)


#this Block consists of four bricks which are arranged like an uppercase gamma (left)
class GammaBlockLeft (Block):
    def __init__(self, parentNode, position, renderer, world, brick):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)
        #self.brick1 = Brick(self.parentNode, x - brickSize, y - halfBrickSize, colour, self)
        #self.brick2 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)
        #self.brick3 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)


#this Block consists of four bricks which are arranged like an uppercase gamma (right - mirror inverted)
class GammaBlockRight (Block):
    def __init__(self, parentNode, position, renderer, world, brick):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        #self.brick1 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)
        #self.brick2 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)
        #self.brick3 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)


# this Block consists of three bricks which are arranged in a line, in the middle a fourth brick is added (left)
class MiddleBlockLeft (Block):
    def __init__(self, parentNode, position, renderer, world, brick):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        #self.brick1 = Brick(self.parentNode, x - brickSize, y - halfBrickSize, colour, self)
        #self.brick2 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)
        #self.brick3 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)


# this Block consists of three bricks which are arranged in a line, in the middle a fourth brick is added (right - mirror inverted)
class MiddleBlockRight (Block):
    def __init__(self, parentNode, position, renderer, world, brick):
        Block.__init__(self, parentNode)
        self.brick0 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        #self.brick1 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)
        #self.brick2 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)
        #self.brick3 = Brick(self.parentNode, x - brickSize, y - halfBrickSize, colour, self)
