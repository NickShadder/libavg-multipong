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
        self.boni = []
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
        self.points = max(0,self.points-points)
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
        self.body.CreateCircleFixture(radius=radius, density=1, restitution=.3,
                                      friction=.01, groupIndex=1, categoryBits=cats['ball'],
                                      maskBits=dontCollideWith('ghost'), userData='ball')
        self.body.CreateCircleFixture(radius=radius, userData='ball', isSensor=True)
        self.nextDir = (random.choice([standardXInertia, -standardXInertia]), random.randint(-10, 10))
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
        self.nextDir = (-standardXInertia, yOffset) if  self.leftPlayer.points > self.rightPlayer.points else (standardXInertia, yOffset)
        self.__appear(lambda:self.nudge())
        
    def __appear(self, stopAction=None):
        wAnim = avg.LinearAnim(self.node, 'width', 500, 1, int(self.node.width))
        hAnim = avg.LinearAnim(self.node, 'height', 500, 1, int(self.node.height))
        angle = 0 if self.nextDir[0]>=0 else math.pi
        aAnim = avg.LinearAnim(self.node, 'angle', 500, math.pi/2, angle)
        avg.ParallelAnim([wAnim, hAnim,aAnim], None, stopAction, 500).start()
    
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
            direction = self.nextDir
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
            if direction is None:
                direction = random.randint(-10, 10), random.randint(-10, 10)
            self.body.linearVelocity = direction

    def changeMortality(self):
        # TODO implement some kind of AI
        g_player.setTimeout(random.choice([2000, 3000, 4000, 5000, 6000]), self.changeMortality) # XXX store ids for stopping when one player wins
        if self.body.active: # just to be sure ;)
            self.flipState()

class BorderLine:
    body = None
    def __init__(self, world, pos1, pos2, restitution = 0, sensor=False, *noCollisions):
        """ the positions are expected to be in meters """
        self.world = world
        if BorderLine.body is None:
            BorderLine.body = world.CreateStaticBody(position=(0, 0))
        BorderLine.body.CreateFixture(shape=b2EdgeShape(vertices=[pos1, pos2]), density=1, isSensor=sensor,
                                restitution=restitution, categoryBits=cats['border'], maskBits=dontCollideWith(*noCollisions))
    def destroy(self):
        if self.body is not None:
            self.world.DestroyBody(self.body)
            self.body = None

# TODO implement class Bonus
class Bonus:
    
    def __init__(self,parentNode, name, game, effect):
        Bonus = avg.SVG('../data/img/char/'+ name + '.svg', False).renderElement('layer1', (150, 150))
        self.game = game
        self.type = name
        self.effect = effect
        self.leftBonus = avg.ImageNode(parent=parentNode,pos= (700,450))
        self.leftBonus.setBitmap(Bonus)    
        self.rightBonus = avg.ImageNode(parent=parentNode,pos= (1050,450))
        self.rightBonus.setBitmap(Bonus)

    def destroy(self):
        self.leftBonus.unlink(True)
        self.leftBonus = None
        self.rightBonus.unlink(True)
        self.rightBonus = None
        self.game.bonusstep = 1
        
    def applyEffect(self, orientation):
        self.effect(orientation)
        
class PersistentBonus(Bonus):
    def __init__(self,parentNode, name, game, effect):
        Bonus.__init__(self, parentNode, name, game, effect)
        self.leftBonus.setEventHandler(avg.CURSORDOWN, avg.TOUCH, lambda e:self.leftPersistentTouch())
        self.rightBonus.setEventHandler(avg.CURSORDOWN, avg.TOUCH, lambda e:self.rightPersistentTouch())
        
    def leftPersistentTouch(self):
        self.game.leftPlayer.boni = self.game.leftPlayer.boni + [self] 
        self.destroy()
        
    def rightPersistentTouch(self):
        self.game.rightPlayer.boni = self.game.rightPlayer.boni + [self]
        self.destroy()
        
class InstantBonus(Bonus):
    def __init__(self,parentNode, name, game, effect):
        self.__init__(self, parentNode, name, game, effect)
        self.leftBonus.setEventHandler(avg.CURSORDOWN, avg.TOUCH, lambda e:self.leftInstantTouch())
        self.rightBonus.setEventHandler(avg.CURSORDOWN, avg.TOUCH, lambda e:self.rightInstantTouch())
        
    def leftInstantTouch(self):
        self.applyEffect("left") 
        self.destroy()
        
    def rightInstantTouch(self):
        self.applyEffect("right")
        self.destroy()  
        

        
        
    
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
    batImgLen = max(1,maxBatSize * PPM / 2)
    batImgWidth = max(1,batImgLen / 10)
    blueBat = avg.SVG('../data/img/char/bat_blue.svg', False).renderElement('layer1', (batImgWidth,batImgLen))
    greenBat = avg.SVG('../data/img/char/bat_green.svg', False).renderElement('layer1', (batImgWidth,batImgLen))
    def __init__(self, renderer, world, parentNode, pos):
        GameObject.__init__(self, renderer, world)
        self.zone = parentNode
        vec = pos[1] - pos[0]
        self.length = max(1,vec.getNorm())
        width = max(1,(maxBatSize * PPM - self.length) / 10)
        angle = math.atan2(vec.y, vec.x)
        self.node = avg.ImageNode(parent=parentNode,size=(width, self.length),angle=angle)
        self.node.setBitmap(Bat.blueBat if parentNode.pos==(0,0)else Bat.greenBat)
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
    
# todo we do not need a class for this 
class Material:
    GLASS = 1, [avg.SVG('../data/img/char/glass.svg', False).renderElement('layer1', (brickSize * PPM, brickSize * PPM)),
                avg.SVG('../data/img/char/glass_shat.svg', False).renderElement('layer1', (brickSize * PPM, brickSize * PPM))]
    # TODO add others

class Brick(GameObject):
    def __init__(self, parentBlock, renderer, world, parentNode, pos, mat=None):
        GameObject.__init__(self, renderer, world)
        self.block, self.hitcount, self.material = parentBlock, 0, mat
        self.parentNode=parentNode
        if self.material is None:
            self.material = random.choice(filter(lambda x:type(x).__name__ == 'tuple', Material.__dict__.values())) # XXX hacky
        self.node = avg.ImageNode(parent=parentBlock.container, pos=pos)
        self.node.setBitmap(self.material[1][0])
        ui.DragRecognizer(self.node, moveHandler=self.onMove)
    
    def onMove(self, e, offset):
        self.block.container.pos += offset
        # todo implement range check
        
    # spawn a physical object
    def materialze(self, pos=None):
        if pos is None:
            pos = (self.node.pos + self.node.pivot) / PPM # TODO this looks like trouble
        self.node.unlink()
        self.parentNode.append_child(self.node)
        fixtureDef = b2FixtureDef (userData='brick', shape=b2PolygonShape (box=(halfBrickSize, halfBrickSize)),
                                  density=1, friction=.1, restitution=1, categoryBits=cats['brick'])
        self.body = self.world.CreateKinematicBody(position=pos, fixture=fixtureDef, userData=self)
    
    def hit(self):
        self.hitcount += 1
        if self.hitcount < len(self.material[1]):
            self.node.setBitmap(self.material[1][self.hitcount])
        else:
            self.destroy() # XXX maybe override destroy for special effects, or call something like vanish first

    def render(self):
        pass # XXX move the empty method to GameObject when the game is ready

class Block:
    form = dict(
    # (bricks, maxLineLength, offset)
    SINGLE = (1,1,0),
    DOUBLE = (2,2,0),
    TRIPLE = (3,3,0),
    EDGE = (3,2,0),
    SQUARE = (4,2,0),
    LINE = (4,4,0),
    SPIECE = (4,2,1),
    LPIECE = (4,3,0),
    TPIECE = (4,3,1)
)
    def __init__(self, parentNode, renderer, world, position, form=None, flip=False, material=None, angle=0):
        self.parentNode, self.renderer, self.world, self.position = parentNode, renderer, world, position
        self.form, self.flip, self.material, self.angle = form, flip, material, angle
        if form is None:
            self.form = random.choice(Block.form.values())
        self.brickList = []
        self.container = avg.DivNode(parent=parentNode,pos=position,angle=angle)
        # XXX maybe set pivot
        brickSizeInPx = brickSize*PPM
        bricks,maxLineLength,offset = self.form
        rightMostPos = (maxLineLength-1)*brickSizeInPx
        line = -1
        for b in range(bricks):
            posInLine = b % maxLineLength
            if posInLine == 0: line += 1
            posX = (line*offset+posInLine)*brickSizeInPx
            if flip: posX = rightMostPos - posX
            posY = line*brickSizeInPx
            self.brickList.append(Brick(self, renderer, world, parentNode, (posX,posY), material))