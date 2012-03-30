'''
Created on 15.02.2012

@author: 2526240
'''

import random
import math
import config

from libavg import avg, ui
from Box2D import b2EdgeShape, b2PolygonShape, b2FixtureDef, b2CircleShape, b2Filter, b2Vec2

from config import PPM, pointsToWin, ballRadius, ghostRadius, brickSize, maxBatSize, bonusTime, brickLines, maxNumOfRubberBricks

cats = {'border':0x0001, 'ghost':0x0002, 'ball':0x0004, 'brick':0x0008, 'redball':0x0010, 'semiborder':0x0020, 'mine':0x0040, 'bat':0x0080, 'rocket':0x0100}
def dontCollideWith(*categories): return reduce(lambda x, y: x ^ y, [cats[el] for el in categories], 0xFFFF)

standardXInertia = 20 * ballRadius # XXX solve more elegantly
g_player = avg.Player.get()
displayWidth = displayHeight = bricksPerLine = None 

class Player:
    def __init__(self, game, avgNode,PTW):
        self.points = 0
        self.other = None
        self.game = game
        self.pointsToWin = PTW
        self.zone = avgNode
        self.left = avgNode.pos == (0, 0)
        avgNode.player = self
        self.pointsToWin = PTW
        angle = math.pi / 2 if self.left else -math.pi / 2
        pos = (avgNode.width, 2) if self.left else (0, avgNode.height - 2)            
        # XXX gameobects may obstruct view of the points!
        self.pointsDisplay = avg.WordsNode(parent=avgNode, pivot=(0, 0), pos=pos, angle=angle,text='Points: 0 / %d' % PTW)
        if self.left:
            self.EndText = avg.WordsNode(parent=avgNode, pivot=(0, 0), pos=(pos[0]-avgNode.width/2 , 50), angle=angle,
                                           text='', fontsize=100)
        else:
            self.EndText = avg.WordsNode(parent=avgNode, pivot=(0, 0), pos=(pos[0]+avgNode.width/2 , avgNode.height-50), angle=angle,
                                           text='', fontsize=100)
        
        self.pointsAnim = None
        self.pointsDisplayMaximalFontSize = int(avgNode.height/20)
        self.pumpingBack = self.pointsDisplay.fontsize
        self.pumpingMax = self.pumpingBack + 8
        
        self.__numOfRubberBricks = 0 # current number of indestructable rubber bricks
        self.__raster = dict()
        self.__nodeRaster = [] # rectNodes to display the margins of the raster
        self.__freeBricks = set()
        pixelBrickSize = brickSize * PPM
        for x in xrange(brickLines):
            for y in xrange(bricksPerLine):
                xPos, yPos = x * pixelBrickSize, y * pixelBrickSize
                if not self.left:
                    xPos = avgNode.width - xPos - pixelBrickSize
                self.__nodeRaster.append(avg.RectNode(parent=avgNode, pos=(xPos, yPos), size=(pixelBrickSize, pixelBrickSize), active=False))
        
    def isLeft(self):
        return self.left
 
    def setEndText(self, text):
        self.EndText.text = text
        
    def addPoint(self, points=1):
        self.points += points
        self.updateDisplay()
        if self.pointsAnim is None or not self.pointsAnim.isRunning():
                self.highLightPointIncreaseByFont()
                
        if self.points >= self.pointsToWin:
            self.highLightPointIncreaseByFont()
            self.game.end(self)

    def highLightPointIncreaseByFont(self):
        self.pointsAnim = avg.LinearAnim(self.pointsDisplay , 'fontsize', 200, self.pumpingBack,
                                                   self.pumpingMax,False,None,self.dehighLightPointIncreaseByFont).start()
            
    def dehighLightPointIncreaseByFont(self):
        self.pointsAnim = avg.LinearAnim(self.pointsDisplay , 'fontsize', 200, self.pumpingMax,
                                                    self.pumpingBack).start()
                                                                                                     
    def penalize(self, points=1):
        self.other.addPoint(points)
#        self.points = max(0, self.points - points)
#        self.updateDisplay()
    
    def updateDisplay(self):
        self.pointsDisplay.text = 'Points: %d / %d' % (self.points, self.pointsToWin)
    
    def getNodeRaster(self):
        return self.__nodeRaster
    
    def getRasterContent(self, x, y):
        if self.__raster.has_key((x, y)):
            return self.__raster[(x, y)]
        return None
    
    def setRasterContent(self, x, y, content):
        self.__raster[(x, y)] = content
        if content.getMaterial() is not Brick.material['RUBBER']:
            self.__freeBricks.add((x, y))
    
    def clearRasterContent(self, x, y):
        if self.__raster.has_key((x, y)):
            del self.__raster[(x, y)]
        if (x, y) in self.__freeBricks:
            self.__freeBricks.remove((x, y))
    
    def bonusFreed(self, x, y):
        self.__freeBricks.add((x, y))
    
    def addBonus(self, bonus):
        if len(self.__freeBricks) > 0:
            (x, y) = self.__freeBricks.pop()
            brick = self.getRasterContent(x, y)
            brick.setBonus(bonus)
            bonus.saveBonus(brick, self.left)
    
    def getNumOfRubberBricks(self):
        return self.__numOfRubberBricks
    
    def incNumOfRubberBricks(self):
        self.__numOfRubberBricks += 1

    def killBricks(self): # XXX test
        copy = self.__raster.copy()
        for x in copy.values():
            x.destroy()
        copy.clear()
            
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
    pic = None
    def __init__(self, game, renderer, world, parentNode, position):
        GameObject.__init__(self, renderer, world)
        self.game = game
        self.parentNode = parentNode
        self.spawnPoint = parentNode.pivot / PPM # XXX maybe make a static class variable
        self.leftPlayer = game.leftPlayer
        self.rightPlayer = game.rightPlayer
        self.lastPlayer = None
        self.node = avg.ImageNode(parent=parentNode)
        self.node.setBitmap(Ball.pic)
        self.body = world.CreateDynamicBody(position=position, userData=self, active=False, bullet=True) # XXX reevaluate bullet-ness
        self.body.CreateCircleFixture(radius=ballRadius, density=1, restitution=.5,
                                      friction=.001, groupIndex=1, categoryBits=cats['ball'],
                                      maskBits=dontCollideWith('ghost'), userData='ball')

        self.body.CreateCircleFixture(radius=ballRadius, userData='ball', isSensor=True)
        self.nextDir = (random.choice([standardXInertia, -standardXInertia]), random.randint(-10, 10))
        self.__appear(lambda:self.nudge())
        
    def setPic(self,pic):
        self.node.setBitmap(pic)
                 
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
        angle = 0 if self.nextDir[0] >= 0 else math.pi
        aAnim = avg.LinearAnim(self.node, 'angle', 500, math.pi / 2, angle)
        avg.ParallelAnim([wAnim, hAnim, aAnim], None, stopAction, 500).start()
    
    def zoneOfPlayer(self):
        if self.node is None:
            return None
        lz, rz = self.leftPlayer.zone, self.rightPlayer.zone
        if lz.getAbsPos((0, 0))[0] < self.node.pos[0] < lz.getAbsPos(lz.size)[0]:
            return self.leftPlayer
        elif rz.getAbsPos((0, 0))[0] < self.node.pos[0] < rz.getAbsPos(rz.size)[0]:
            return self.rightPlayer
        return None
        
    def invert(self):
        self.body.linearVelocity = -self.body.linearVelocity
        #self.body.linearVelocity = (-self.body.linearVelocity[0],-self.body.linearVelocity[1])
        
    def nudge(self, direction=None):
        self.body.active = True
        self.body.angularVelocity = 0
        self.body.angle = 0
        if direction is None:
            direction = self.nextDir
        self.body.linearVelocity = direction
        self.render()

class Rocket(GameObject):
    pic = None
    highLightpic = None
    def __init__(self, game, player, renderer, world, parentNode, position, vel):
        GameObject.__init__(self, renderer, world)
        self.owner = player
        self.parentNode = parentNode
        self.node = avg.ImageNode(parent=parentNode)
        self.node.setBitmap(Rocket.pic)
        self.body = world.CreateDynamicBody(position=position, userData=self, active=False, bullet=True) # XXX reevaluate bullet-ness
        self.body.CreateCircleFixture(radius=ballRadius, density=1, restitution=.3,
                                      friction=.01, groupIndex= -3, maskBits=dontCollideWith('border', 'rocket', 'ghost', 'brick','semiborder','mine'), 
                                      categoryBits=cats['rocket'], userData='rocket')

        self.body.CreateCircleFixture(radius=ballRadius, userData='rocket', isSensor=True)
        self.nextDir = (2*vel, 0)
        self.__appear(lambda:self.nudge())
        g_player.setTimeout(2000,self.destroy)
    
    def getOwner(self):
        return self.owner
    
    def render(self):
        pos = self.body.position * PPM - self.node.size / 2
        self.node.pos = (pos[0], pos[1])
            
    def __appear(self, stopAction=None):
        wAnim = avg.LinearAnim(self.node, 'width', 500, 1, int(self.node.width))
        hAnim = avg.LinearAnim(self.node, 'height', 500, 1, int(self.node.height))
        avg.ParallelAnim([wAnim, hAnim], None, stopAction, 500).start()
        
    def nudge(self, direction=None):
        if self is not None and self.body is not None:
            self.body.active = True
            if direction is None:
                direction = self.nextDir
            self.body.linearVelocity = direction
            self.render()
        
    def hit(self):
        self.destroy()

class Mine(Ball):
    leftPic = rightPic = None
    def __init__(self, game, parentNode, owner):
        position = (random.randint(0, (int)(parentNode.width / PPM)), random.randint(0, (int)(parentNode.height / PPM)))
        Ball.__init__(self, game, game.renderer, game.world, parentNode, position)
        self.owner = owner
        self.node.setBitmap(Mine.leftPic if owner.isLeft() else Mine.rightPic)
        self.body.active = True
        self.body.userData = self
        filterdef = b2Filter(groupIndex= -1, categoryBits=cats['mine'], maskBits=dontCollideWith('ghost', 'ball', 'bat'))        
        for fix in self.body.fixtures:
            fix.userData = 'mine'
            fix.filterData = filterdef
        # TODO the mine shouldn't live forever, should it?
            
    def getOwner(self):
        return self.owner

    def hit(self):
        self.destroy()

    # Override
    def nudge(self, direction=None):
        pass
            
class RedBall(Ball):
    pic = None
    def __init__(self, game, parentNode, position, left):
        Ball.__init__(self, game, game.renderer, game.world, parentNode, position)
        self.node.setBitmap(RedBall.pic)
        self.left = left
        self.body.userData = self
        filterdef = b2Filter(groupIndex= -1, categoryBits=cats['redball'], maskBits=dontCollideWith('ball', 'redball', 'mine'))
        for fix in self.body.fixtures:
            fix.userData = 'redball'
            fix.filterData = filterdef        
    # Override
    def nudge(self, direction=None):
        self.body.active = True
        speedX = -25 # XXX tweak
        if self.left:
            speedX = -speedX
        self.body.linearVelocity = (speedX, random.randint(-10, 10))
              
    def hit(self):
        self.destroy()

class GhostBall:
    def __init__(self, parentNode, y, left):
        diameter = 2 * ballRadius * PPM
        self.node = avg.ImageNode(parent=parentNode, size=(diameter, diameter))
        self.node.setBitmap(Ball.pic)
        width = int(parentNode.width)
        start = -diameter, y
        end = width, y
        if not left: 
            start, end = end, start
            self.node.angle = math.pi
        avg.LinearAnim(self.node, 'pos', width, start, end, False, None, self.destroy).start()                 
        
    def destroy(self):
        if self.node is not None:
            self.node.active = False
            self.node.unlink(True)
            self.node = None   

class SemipermeableShield:
    pic = None
    def __init__(self, game, left, *noCollisions):
        self.world = game.world
        self.game = game
        self.left = left
        self.node = avg.ImageNode(parent=game.display)
        displayThird = displayWidth / 3
        x = 2 * displayThird
        if left:
            self.node.angle = math.pi
            x = displayThird
        self.node.pos = x, 0
        self.node.setBitmap(SemipermeableShield.pic)
        
        self.body = self.world.CreateStaticBody(position=(x / PPM + .5, displayHeight / (2 * PPM)), userData=self)
        self.body.CreateFixture(shape=b2PolygonShape(box=(.5, displayHeight / (2 * PPM), (0, 0), math.pi)), density=1,
                                restitution=1, groupIndex= -2, categoryBits=cats['semiborder'], userData='semiborder',
                                maskBits=dontCollideWith(*noCollisions))
    
    def destroy(self):
        if self.body is not None:
            self.world.DestroyBody(self.body)
            self.body = None
        if self.node is not None:
            self.node.active = False
            self.node.unlink(True)
            self.node = None  
            
    def ownedByLeft(self):
        return self.left

class Ghost(GameObject):
    pics = {}
    def __init__(self, renderer, game, parentNode, position, name, owner=None, mortal=1):
        GameObject.__init__(self, renderer, game.world)
        self.parentNode = parentNode        
        self.spawnPoint = position
        self.game = game
        self.name = name
        self.movement = self.changing = self.aging = None
        self.diameter = 2 * ballRadius * PPM
        self.trend = None
        self.owner = owner
        if owner is not None:
            self.aging = g_player.setTimeout(60000,self.destroy)
        self.mortal = mortal
        self.node = avg.ImageNode(parent=parentNode, opacity=.85)
        # self.setShadow('ADD8E6')
        ghostUpper = b2FixtureDef(userData='ghost', shape=b2CircleShape(radius=ghostRadius),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'], maskBits=dontCollideWith('ball'))
        ghostLower = b2FixtureDef(userData='ghost', shape=b2PolygonShape(box=(ghostRadius, ghostRadius / 2, (0, -ghostRadius / 2), 0)),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'], maskBits=dontCollideWith('ball'))
        self.body = game.world.CreateDynamicBody(position=position, fixtures=[ghostUpper, ghostLower],
                                            userData=self, fixedRotation=True)
        self.changeMortality()
        self.render()
        self.move()


    
    def resetTrend(self):
        self.trend = None 
    
    def getDir(self):
        return self.body.linearVelocity
    
    def getOwner(self):
        return self.owner
             
    def flipState(self):
        if self.node is not None and self.body.active:
            self.mortal ^= 1
            if self.mortal:
                self.node.setBitmap(Ghost.pics['blue'])
            else:
                self.node.setBitmap(Ghost.pics[self.name])
        
    def render(self):
        pos = self.body.position * PPM - self.node.size / 2
        self.node.pos = (pos[0], pos[1])
        self.node.angle = self.body.angle
             
    def reSpawn(self, pos=None):
        self.body.active = False
        if self.movement is not None:
            g_player.clearInterval(self.movement)
            self.movement = None
        if pos is None:
            pos = self.spawnPoint
        avg.fadeOut(self.node, 1000, lambda:self.__kill(pos))
    
    def __kill(self, pos):
        if self.node is not None:
            self.node.active = False
            g_player.setTimeout(3000, lambda:self.__reAppear(pos)) # XXX adjust timeout or make it configgable 
    
    def __reAppear(self, pos):
        if self.body is not None:
            self.body.position = pos
            self.mortal = 0 # ghost respawns in immortal state
            self.node.setBitmap(Ghost.pics[self.name])
            self.render()
            self.node.active = True
            avg.fadeIn(self.node, 1000, .85, self.__activateBody)
        
    def __activateBody(self):
        if self.body is not None:
            self.body.active = True
            self.move()
        
    def move(self, direction=None):
        # TODO implement some kind of AI
        self.movement = g_player.setTimeout(random.randint(500, 2500), self.move)
        if self.body is not None and self.body.active: # just to be sure ;)
            if direction is None:
                if self.trend == 'left':
                    direction = random.randint(-10, 0), random.randint(-10, 10)
                elif self.trend == 'right':
                    direction = random.randint(0, 10), random.randint(-10, 10)
                else:
                    direction = random.randint(-10, 10), random.randint(-10, 10)
            self.body.linearVelocity = direction
    
    def setTrend(self, trend):
        if self.trend is None:
            self.trend = trend
            g_player.setTimeout(20000, self.resetTrend)
    
    def stop(self):
        if self.body is not None:
            if self.movement is not None:
                g_player.clearInterval(self.movement)
            self.body.linearVelocity = (0, 0)
            self.movement = g_player.setTimeout(2000, self.move)    
        
    def changeMortality(self):
        # TODO implement some kind of AI
        self.changing = g_player.setTimeout(random.choice([2000, 3000, 4000, 5000, 6000]), self.changeMortality) # XXX store ids for stopping when one player wins
        if self.body is not None and self.body.active: # just to be sure ;)
            self.flipState()
  
    # override
    def destroy(self):
        GameObject.destroy(self)
        if self.movement is not None:
            g_player.clearInterval(self.movement)
            self.movement = None
        if self.changing is not None:
            g_player.clearInterval(self.changing)
            self.changing = None
        if self.aging is not None:
            g_player.clearInterval(self.aging)
            self.aging = None

class BorderLine:
    body = None
    def __init__(self, world, pos1, pos2, restitution=0, sensor=False, *noCollisions):
        """ the positions are expected to be in meters """
        self.world = world
        if BorderLine.body is None:
            BorderLine.body = world.CreateStaticBody(position=(0, 0))
        self.fix = BorderLine.body.CreateFixture(shape=b2EdgeShape(vertices=[pos1, pos2]), density=1, isSensor=sensor,
                                restitution=restitution, categoryBits=cats['border'], maskBits=dontCollideWith(*noCollisions))
    def destroy(self):
        if self.body is not None:
            self.world.DestroyBody(self.body)
            self.body = None
            
class Tower:
    pic = None
    def __init__(self, game, position, number, left=False):
        self.game = game
        self.left = left
        self.firing = None
        self.node = avg.ImageNode(parent=game.display, pos=position)
        # game.display.reorderChild(self.node, 6) 
        self.node.setBitmap(Tower.pic)
        ballOffset = ballRadius, 2 * ballRadius
        self.firingpos = (b2Vec2(position) + self.node.size) / PPM - ballOffset
        if left:
            self.node.angle = math.pi
            self.firingpos = b2Vec2(position) / PPM + ballOffset
            
        g_player.setTimeout(1000 + (number * 1000), self.fire)
        g_player.setTimeout(30000 + (number * 1000), self.destroy)
            
    def fire(self):
        if self.node is not None:
            self.game.getRedBalls().append(RedBall(self.game, self.game.display, self.firingpos, self.left))
            self.firing = g_player.setTimeout(3000, self.fire)
        
    def destroy(self):
        if self.node is not None:
            self.node.active = False
            self.node.unlink(True)
            self.node = None
        if self.firing is not None:
            g_player.clearInterval(self.firing)
    
class Bonus:    
    pics = {}
    texts = {
                      'newBlock': (config.newBlockText ,'wave'),
                      'wave': (config.waveText,'tower'),
                      'tower': (config.towerText,'pacShot'),
                      'pacShot': (config.pacShotText,'stopGhosts'),
                      'stopGhosts': (config.stopGhostsText,'flipGhosts'),
                      'flipGhosts': (config.flipGhostsText,'invertPac'),
                      'invertPac': (config.invertPacText,'shield'),
                      'shield': (config.shieldText,'addOwnGhost'),
                      'addOwnGhost': (config.addOwnGhostText,'hideGhosts'),
                      'hideGhosts': (config.hideGhostsText,'resetGhosts'),
                      'resetGhosts': (config.resetGhostsText,'sendGhostsToOtherSide'),
                      'sendGhostsToOtherSide': (config.sendGhostsToOtherSideText,'mine'),
                      'mine': (config.mineText,'None')
        }
    
    
    def __init__(self, game, (name, effect)):
        parentNode = game.display
        self.highLights = []   
        displayWidth = parentNode.width
        displayHeight = parentNode.height
        self.name = name 
        self.width, self.height = displayWidth / 15, parentNode.width / 15
        self.pic = Bonus.pics[name]
        self.parentNode, self.game, self.world = parentNode, game, game.world
        self.effect = effect
        self.leftBonus = avg.ImageNode(parent=parentNode, pos=(displayWidth / 3, displayHeight / 2 - (self.height / 2)), angle=math.pi/2)
        self.leftBonus.setBitmap(self.pic)
        
        self.rightBonus = avg.ImageNode(parent=parentNode, pos=(2 * displayWidth / 3 - self.width, displayHeight / 2 - (self.height / 2)), angle=-math.pi/2)
        self.rightBonus.setBitmap(self.pic)
        self.leftBonus.setEventHandler(avg.CURSORDOWN, avg.TOUCH, self.onClick)
        self.rightBonus.setEventHandler(avg.CURSORDOWN, avg.TOUCH, self.onClick)
        self.timeout = g_player.setTimeout(bonusTime * 1000, self.vanish)
        self.isTutorial = False
        self.lastExplNodeLeft = None
        self.lastExplNodeRight = None
        self.res = None
        self.explStarted = 0
        self.player = None
        self.item = None
        
    def onClick(self, event):
        self.res = event.node == self.leftBonus
        g_player.clearInterval(self.timeout)
        if self.res:
            self.player = self.game.leftPlayer
        else:
            self.player = self.game.rightPlayer
            
        if self.isTutorial and not self.explStarted:
            self.explStarted = 1
            self.cleanUp()
            self.field1 = self.game.field1
            self.field2 = self.game.field2
            self.item = self.texts[self.name]
            self.wordsNodeUp = avg.WordsNode(
                                    parent=self.field2,
                                    pivot=(0, 0),
                                    text=self.item[0],
                                    wrapmode="wordchar",
                                    font='Comic Sans MS',
                                    color="00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle= -math.pi / 2)
        
            self.highLights.append(self.wordsNodeUp)
            avg.LinearAnim(self.wordsNodeUp, 'pos', 600, (0, -self.wordsNodeUp.width),
                                                    (0, self.wordsNodeUp.width)).start()                                 
            self.wordsNodeDown = avg.WordsNode(
                                    parent=self.field1,
                                    pivot=(0, 0),
                                    text=self.item[0],
                                    wrapmode="wordchar",
                                    font='Comic Sans MS',
                                    color="00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle=math.pi / 2)
        
            self.highLights.append(self.wordsNodeDown)  
            avg.LinearAnim(self.wordsNodeDown, 'pos', 600, (self.field1.width, self.wordsNodeDown.getParent().height),
                                                    (self.field1.width, self.wordsNodeDown.getParent().height - self.wordsNodeDown.width)).start()        
                                                                                                                                                                               
            
            self.lastExplNodeLeft = self.wordsNodeDown
            self.lastExplNodeRight = self.wordsNodeUp
            g_player.setTimeout(config.bonusVanishTime, self.nextBonus)
            
        elif self.isTutorial and self.explStarted:
            self.applyEffect(self.player)
            
        else:
            self.vanish()
            
        return self.res

    def nextBonus(self):     
#        if self.explStarted:
#            self.vanish()

        if self.isTutorial:
            self.explStarted = 1
            if not self.item[1] == 'None':  
                self.cleanUp()
                self.vanish()
                self.giveBonus(self.item[1]).setupTutorial(self.wordsNodeUp,self.wordsNodeDown)
            else:
                self.lastExplNodeLeft = self.wordsNodeDown
                self.lastExplNodeRight = self.wordsNodeUp
                g_player.setTimeout(config.bonusVanishTime, self.vanish)
                g_player.setTimeout(config.bonusVanishTime, self.cleanUp)
                self.game.menuButton = self.game.makeButtonInMiddle('menu', self.game.display, 0, self.game.clearDisplay)

        return self.res
    
    def cleanUp(self):
        killNode(self.lastExplNodeLeft)
        killNode(self.lastExplNodeRight)
        
    def setPositionLeft(self,position):
        self.leftBonus.pos = position
         
    def setPositionRight(self,position):
        self.rightBonus.pos = position
        
    def setupTutorial(self,lastExplNodeLeft=None,lastExplNodeRight=None):
        self.lastExplNodeLeft = lastExplNodeLeft
        self.lastExplNodeRight = lastExplNodeRight
        self.isTutorial = True
        g_player.clearInterval(self.timeout)
        
    def vanish(self):
        if self.leftBonus is not None:
            self.leftBonus.active = False
            self.leftBonus.unlink(True)
            self.leftBonus = None
        if self.rightBonus is not None:
            self.rightBonus.active = False
            self.rightBonus.unlink(True)
            self.rightBonus = None
        if self.timeout is not None:
            g_player.clearInterval(self.timeout)
            self.timeout = None
        
    def applyEffect(self, player):
        self.effect(self, player)
    
    def saveBonus(self, brick, left):
        hSize = .85 * brickSize * PPM
        position = (brickSize * PPM - hSize) / 2
        if left:
            angle = math.pi/2
        else:
            angle = -math.pi/2
        self.__node = avg.ImageNode(parent=brick.getDivNode(), pos=(position, position), size=(hSize, hSize), angle=angle)
        self.__node.setBitmap(self.pic)
        self.__node.setEventHandler(avg.CURSORDOWN, avg.TOUCH, lambda e, brick=brick: self.__useBonus(brick))
    
    def destroy(self, brick):
        brick.removeBonus()
        self.__node.active = False # XXX animate?
        self.__node.unlink(True)        
    
    def __useBonus(self, brick):
        self.destroy(brick)
        self.applyEffect(brick.getPlayer())
        
    def pacShot(self, player):
        height = self.parentNode.height
        # XXX they should be spawned on random heights
        GhostBall(self.parentNode, height / 4, player.isLeft())
        GhostBall(self.parentNode, height / 2, player.isLeft())
        GhostBall(self.parentNode, (3 * height) / 4, player.isLeft())
        
    def flipGhostStates(self, player=None):
        for g in self.game.getGhosts():
            g.flipState()

    def stopGhosts(self, player=None):
        ghosts = self.game.getGhosts()
        if ghosts:
            for g in ghosts:
                g.stop()
            
    def invertPac(self, player=None):    
        for b in self.game.getBalls():
            b.invert()
                
    def hideGhosts(self, player=None):
        self.game.killGhosts()
        
    def resetGhosts(self, player=None):
        self.hideGhosts(player)  # kill off all ghosts
        self.game.createGhosts() # restore the original four ghosts 
         
    def addGhost(self, player):        
        if player.isLeft():
            name = "ghostOfBlue"
        else:
            name = "ghostOfGreen"            
        self.game.ghosts.append(Ghost(self.game.renderer, self.game, self.parentNode, self.game.middle - (0, (ballRadius + ghostRadius) * 2), name, player))
        
    def sendGhostsToOpponent(self, player):
        for g in self.game.getGhosts():
            if player.isLeft():
                g.setTrend('right')
            else:
                g.setTrend('left')
                
                                  
    def setTowers(self, player):
        thirdWidth = self.parentNode.width / 3
        quarterHeight = self.parentNode.height / 4
        if player.isLeft():
            x = thirdWidth - 4 * ballRadius * PPM
        else:
            x = 2 * thirdWidth
        for i in range(1, 4):
            Tower(self.game, (x, i * quarterHeight), i, player.isLeft())        
            
    def setMine(self, player=None):
        Mine(self.game, self.parentNode, player)
          
    def newBlock(self, player): 
        height = (self.parentNode.height / 2) - (brickSize * PPM)
        
        width = self.parentNode.width
        if player.isLeft():
            Block(self.game.display, self.game.renderer, self.world, (width / 3 - (brickSize * 5 * PPM), height), self.game.leftPlayer, random.choice(Block.form.values()))
        else:
            Block(self.game.display, self.game.renderer, self.world, (2 * width / 3, height), self.game.rightPlayer, random.choice(Block.form.values()))
            
    def buildShield(self, player):
        s = SemipermeableShield(self.game, player.isLeft(), 'ghost')
        g_player.setTimeout(10000, s.destroy) # XXX tweak time
   
    def startWave(self, player):
        for i in range(0, 30):
            if player.isLeft():
                pos = (brickSize * brickLines + ghostRadius, (2 * ballRadius) * i)
                vel = 50
            else:
                vel = -50
                pos =  (self.parentNode.size[0] / PPM - (brickSize * brickLines + ghostRadius), (2 * ballRadius) * i)
            Rocket(self.game, player, self.game.renderer, self.world, self.parentNode, pos, vel)
    
    def giveBonus(self,name):
        if PersistentBonus.boni.has_key(name):
            self.game.bonus = PersistentBonus(self.game, (name, PersistentBonus.boni[name]))
        elif InstantBonus.boni.has_key(name):
            self.game.bonus = InstantBonus(self.game, (name, InstantBonus.boni[name]))
        return self.game.bonus
        
class PersistentBonus(Bonus):
    probs = [('pacShot', 2),
             ('stopGhosts', 2),
             ('flipGhosts', 2),
             ('tower', 4),
             ('invertPac', 2),
             ('shield', 4),
             ('wave', 5)
             ]
    
    boni = dict(
                pacShot=Bonus.pacShot,
                stopGhosts=Bonus.stopGhosts,
                flipGhosts=Bonus.flipGhostStates,
                tower=Bonus.setTowers,
                invertPac=Bonus.invertPac,
                shield=Bonus.buildShield,
                wave=Bonus.startWave
                )
            
    def __init__(self, game, (name, effect)):
        Bonus.__init__(self, game, (name, effect))
    
    def onClick(self, event):
        (self.game.leftPlayer if Bonus.onClick(self, event) else self.game.rightPlayer).addBonus(self)  
        
class InstantBonus(Bonus):
    probs = [('newBlock', 3),
             ('addOwnGhost', 4),
             ('hideGhosts', 2),
             ('resetGhosts', 2.5),
             ('sendGhostsToOtherSide', 5),
             ('mine', 2)
             ]
    boni = dict(newBlock=Bonus.newBlock,
                addOwnGhost=Bonus.addGhost,
                hideGhosts=Bonus.hideGhosts,
                resetGhosts=Bonus.resetGhosts,
                sendGhostsToOtherSide=Bonus.sendGhostsToOpponent,
                mine=Bonus.setMine
                )

    def __init__(self, game, (name, effect)):
        Bonus.__init__(self, game, (name, effect))
        
    def onClick(self, event):
        self.applyEffect(self.game.leftPlayer if Bonus.onClick(self, event) else self.game.rightPlayer)

class Bat(GameObject): # XXX maybe ghosts should be able to penetrate the bat
    blueBat = greenBat = None
    def __init__(self, renderer, world, parentNode, pos):
        GameObject.__init__(self, renderer, world)
        self.zone = parentNode
        vec = pos[1] - pos[0]
        self.length = max(1, vec.getNorm())
        width = max(1, (maxBatSize * PPM - self.length) / 10)
        angle = math.atan2(vec.y, vec.x)
        self.node = avg.ImageNode(parent=parentNode, size=(width, self.length), angle=angle)
        self.node.setBitmap(Bat.blueBat if parentNode.pos == (0, 0)else Bat.greenBat)
        mid = (pos[0] + pos[1]) / (2 * PPM)
        width = width / (2 * PPM)
        length = self.length / (2 * PPM)
        shapedef = b2PolygonShape(box=(length, width))
        fixturedef = b2FixtureDef(userData='bat', shape=shapedef, density=1, restitution=1, friction=.02, groupIndex=1,
                                  categoryBits=cats['bat'])
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

class Brick(GameObject):
    material = {}
    def __init__(self, parentBlock, container, renderer, world, parentNode, pos, mat=None):
        GameObject.__init__(self, renderer, world)
        self.__block = parentBlock
        self.__hitcount = 0
        self.__material = mat
        self.__parentNode = parentNode
        if self.__material is None:
            mats = Brick.material.values()[:]
            if (parentBlock.getForm() != Block.form['SINGLE'] or 
                parentBlock.getPlayer().getNumOfRubberBricks() > maxNumOfRubberBricks):
                mats.remove(Brick.material['RUBBER'])
            self.__material = random.choice(mats)
            del mats[:]
        self.node = avg.ImageNode(parent = container, pos=pos)
        self.node.setBitmap(self.__material[0])
        self.__divNode = None
        self.__index = None
        self.__bonus = None

    # spawn a physical object
    def materialize(self, x, y, pos=None):
        if pos is None:
            pos = (self.node.pos + self.node.pivot) / PPM # TODO this looks like trouble
        self.node.unlink()
        self.__parentNode.appendChild(self.node)
        self.__divNode = avg.DivNode(parent=self.__parentNode, pos=self.node.pos, size=self.node.size)
        halfBrickSize = brickSize / 2
        fixtureDef = b2FixtureDef (userData='brick', shape=b2PolygonShape (box=(halfBrickSize, halfBrickSize)),
                                  density=1, friction=.03, restitution=1, categoryBits=cats['brick'])
        self.body = self.world.CreateStaticBody(position=pos, userData=self)
        self.body.CreateFixture(fixtureDef)
        self.__index = (x, y)
        if self.__material == Brick.material['RUBBER']:
            self.getPlayer().incNumOfRubberBricks()
    
    def hit(self):
        if self.node is None:
            return
        self.__hitcount += 1
        if self.__hitcount < len(self.__material):
            if self.__material[self.__hitcount] is None: # the material is unkillable
                self.__hitcount -= 1
            else:
                self.node.setBitmap(self.__material[self.__hitcount])
        else:            
            self.destroy() # XXX maybe override destroy for special effects, or call something like vanish first
    
    def setBonus(self, bonus):
        self.__bonus = bonus
    
    def removeBonus(self):
        self.__bonus = None
        if self.__material is Brick.material['BUBBLE']:
            self.destroy()
        elif self.__block.getPlayer().getRasterContent(self.__index[0], self.__index[1]) is not None:
            self.getPlayer().bonusFreed(self.__index[0], self.__index[1])
    
    def getDivNode(self):
        return self.__divNode
    
    def getPlayer(self):
        return self.__block.getPlayer()
    
    def getMaterial(self):
        return self.__material

    def render(self):
        pass # XXX move the empty method to GameObject when the game is ready

    # override
    def destroy(self):
        self.__block.getPlayer().clearRasterContent(self.__index[0], self.__index[1])
        if self.__bonus is not None:
            self.__material = None
            self.__bonus.destroy(self)
        if self.__divNode is not None:
            self.__divNode.unlink(True)
        GameObject.destroy(self)

class Block:
    form = dict(
    # (bricks, maxLineLength, offset)
    SINGLE=(1, 1, 0),
    DOUBLE=(2, 2, 0),
    TRIPLE=(3, 3, 0),
    EDGE=(3, 2, 0),
    SQUARE=(4, 2, 0),
    LINE=(4, 4, 0),
    SPIECE=(4, 2, 1),
    LPIECE=(4, 3, 0),
    TPIECE=(4, 3, 1))
    def __init__(self, parentNode, renderer, world, position, player, form=None, flip=False, material=None, angle=0, vanishLater=False, movable = True):        
        self.__parentNode = parentNode
        self.__player = player
        self.__form = form
        if form is None:
            self.__form = random.choice(Block.form.values())
        self.__brickList = []
        self.__container = avg.DivNode(parent=parentNode, pos=position, angle=angle)
        brickSizeInPx = brickSize * PPM
        bricks, maxLineLength, offset = self.__form
        rightMostPos = (maxLineLength - 1) * brickSizeInPx
        line = -1
        for b in range(bricks):
            posInLine = b % maxLineLength
            if posInLine == 0: line += 1
            posX = (line * offset + posInLine) * brickSizeInPx
            if flip: posX = rightMostPos - posX
            posY = line * brickSizeInPx
            self.__brickList.append(Brick(self, self.__container, renderer, world, parentNode, (posX, posY), material))
        self.__widthDisplay = parentNode.width
        self.__widthThird = self.__widthDisplay / 3
        self.__alive = False
        if not movable:
            self.__alive = True
            self.__moveEnd(False)
        else:
            timeout = 10000 if vanishLater else 3000
            self.__timeCall = g_player.setTimeout(timeout, self.__vanish)
            if self.__container is not None:
                ui.DragRecognizer(self.__container, moveHandler=self.__onMove, endHandler=self.__moveEnd, coordSysNode = self.__brickList[0].node)
    
    def __onMove(self, e, offset):
        if self.__timeCall is not None:
            g_player.clearInterval(self.__timeCall)
            self.__timeCall = None
        self.__displayRaster(True)
        self.__container.pos += offset
        self.__testInsertion()
    
    def __testInsertion(self):
        possible = True     
        for b in self.__brickList:
            (x, y) = self.__calculateIndices(b.node.pos)
            if ((x >= brickLines) or (y >= bricksPerLine) or
                (x < 0) or (y < 0) or 
                self.__player.getRasterContent(x, y) is not None):
                possible = False
                break
        if possible:
            self.__colourGreen()
        else:
            self.__colourRed()
    
    def __calculateIndices(self, position):
        pixelBrickSize = brickSize * PPM
        if self.__player.isLeft():
            x = int(round((position[0] + self.__container.pos[0]) / pixelBrickSize))
        else:
            x = int(round((self.__parentNode.width - position[0] - self.__container.pos[0] - pixelBrickSize) / pixelBrickSize))
        y = int(round((position[1] + self.__container.pos[1]) / pixelBrickSize))      
        return (x, y)
    
    def __colourRed(self):
        for b in self.__brickList:
            b.node.intensity = (1, 0, 0)
            self.__alive = False
    
    def __colourGreen(self):
        for b in self.__brickList:
            b.node.intensity = (0, 1, 0)
            self.__alive = True
    
    def __vanish(self):
        for b in self.__brickList:
            if b.node is not None:
                b.node.active = False
                b.node.unlink(True)
                b.node = None
        if self.__container is not None:
            self.__container.unlink(True)
        self.__displayRaster(False)
        if self.__timeCall is not None:
            g_player.clearInterval(self.__timeCall)
            self.__timeCall = None
    
    def __moveEnd(self, tr):
#        self.__container.angle = round(2 * self.__container.angle / math.pi) * math.pi / 2
        pixelBrickSize = brickSize * PPM
        if not self.__alive:
            self.__timeCall = g_player.setTimeout(1000, self.__vanish)
        else:
            for b in self.__brickList:
                b.node.intensity = (1, 1, 1)
                (x, y) = self.__calculateIndices(b.node.pos)
                xPos, yPos = x * pixelBrickSize, y * pixelBrickSize
                if not self.__player.isLeft():
                    xPos = self.__parentNode.size[0] - xPos - pixelBrickSize    
                self.__player.setRasterContent(x, y, b)
                b.node.pos = (xPos, yPos)
                b.node.sensitive = False
                b.materialize(x, y)
            self.__container.active = False
            self.__container.unlink(True)
            self.__displayRaster(False)
                
    def __displayRaster(self, on):
        for n in self.__player.getNodeRaster():
            n.active = on        
    
    def getPlayer(self):
        return self.__player
    
    def getForm(self):
        return self.__form

class TetrisBar:
    picBlue = None
    picGreen = None
    def __init__(self, parentNode, callBack=None, time=config.tetrisTutorial, left=True): 
        self.node = avg.ImageNode(parent=parentNode, opacity = 0.7)
        # self.callBack = callBack
        offset = 10
        if left:
            self.node.setBitmap(self.picBlue)
            self.node.pos = (offset, parentNode.height - self.node.height - offset)
            avg.LinearAnim(self.node , 'width', time, self.node.width, 1, False, None, self.destroy).start()
        else:
            self.node.setBitmap(self.picGreen)
            self.node.angle = math.pi
            self.node.pos = (parentNode.width - self.node.width - offset, offset)
            wAnim = avg.LinearAnim(self.node, 'width', time, self.node.width, 1)
            xAnim = avg.LinearAnim(self.node, 'x', time, self.node.x, parentNode.width - offset)
            avg.ParallelAnim([xAnim, wAnim], None, self.destroy, time).start()
            
    def destroy(self):
        self.node.active = False
        self.node.unlink(True)
        self.node = None
#        if self.callBack is not None:
#            self.callBack()

class Tutorial:
    arrowPic = None
    def __init__(self,game):
        self.parentNode = game.display
        self.game = game
    
        self.highLightText = ''
        self.highLights = []
    
    def end(self):
        for node in self.highLights:
            node.active = False
            node.unlink(True)
            node = None       

class BallTutorial(Tutorial):
    def __init__(self,game):
        Tutorial.__init__(self,game)
        self.spawnPoint = self.parentNode.pivot / PPM
        self.highLightText = ("The ball (pacman) spawns in the middle.<br/>" + 
        "Don't let him reach your edge of the table.<br/>" + 
        "You can spawn a bat on your field by touching any two points on it.<br/>" + 
        "They shouldn't be spaced too far though.<br/>" + "You can try it now.")
        
    def start(self):
        # UP
        self.highLightNodeUp = avg.ImageNode(parent=self.parentNode, opacity=1, angle=math.pi / 2)
        self.highLights.append(self.highLightNodeUp)
        self.highLightNodeUp.setBitmap(self.arrowPic) 
        picWidth = self.highLightNodeUp.width
        picHeight = self.highLightNodeUp.height
        highLightNodeUpStartPosition = (self.spawnPoint[0] * PPM - picWidth / 2, 0) 
        highLightNodeUpEndPosition = (self.spawnPoint[0] * PPM - picWidth / 2, self.spawnPoint[1] * PPM - picHeight - (2 * ballRadius * PPM)) 
        
        avg.LinearAnim(self.highLightNodeUp, 'pos', 600, highLightNodeUpStartPosition,
                                                    highLightNodeUpEndPosition).start()
        # UP TEXT 
        self.wordsNodeUp = avg.WordsNode(
                                    parent=self.game.rightPlayer.zone,
                                    pivot=(0, 0),
                                    text=self.highLightText,
                                    wrapmode="wordchar",
                                    font='Comic Sans MS',
                                    color="00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle= -math.pi / 2)
        
        self.highLights.append(self.wordsNodeUp)
        avg.LinearAnim(self.wordsNodeUp, 'pos', 600, (0, -self.wordsNodeUp.width),
                                                    (0, self.wordsNodeUp.width)).start() 
                                                                    
        # DOWN
        self.highLightNodeDown = avg.ImageNode(parent=self.parentNode, opacity=1, angle= -math.pi / 2)
        self.highLights.append(self.highLightNodeDown)
        self.highLightNodeDown.setBitmap(self.arrowPic)
        highLightNodeDownStartPosition = (self.spawnPoint[0] * PPM - picWidth / 2, self.parentNode.height)
        highLightNodeDownEndPosition = (self.spawnPoint[0] * PPM - picWidth / 2, self.spawnPoint[1] * PPM + picHeight) 
        
        
        avg.LinearAnim(self.highLightNodeDown , 'pos', 600, highLightNodeDownStartPosition,
                                                    highLightNodeDownEndPosition).start()     
        
        # DOWN TEXT 
        self.wordsNodeDown = avg.WordsNode(
                                    parent=self.game.leftPlayer.zone,
                                    pivot=(0, 0),
                                    text=self.highLightText,
                                    wrapmode="wordchar",
                                    font='Comic Sans MS',
                                    color="00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle=math.pi / 2)
        
        self.highLights.append(self.wordsNodeDown)  
        avg.LinearAnim(self.wordsNodeDown, 'pos', 600, (self.game.leftPlayer.zone.width, self.parentNode.height),
                                                    (self.game.leftPlayer.zone.width, self.parentNode.height - self.wordsNodeDown.width)).start()                                                                                                                                           
        g_player.setTimeout(config.ballTutorial, self.end) 

class GhostTutorial(Tutorial):
    def __init__(self,game):
        Tutorial.__init__(self,game)
        self.field1 = game.leftPlayer.zone
        self.field2 = game.rightPlayer.zone
        
        self.highLightText = ("These are ghosts.<br/>" +
                              "They change their color.<br/>"+
                              "The pacman eats a blue ghost and spawns another pacman.<br/>"+  
                              "If your bat contacted the pacman last, you will get a point.<br/>"+
                              "If the ghost is not blue, he will eat the pacman.<br/>"+
                              "If it happens on your field, you will lose a point.<br/>") # XXX maybe update if we decide that players no longer lose points) 
        
    def start(self):
        for ghost in self.game.ghosts:
            self.highLightGhost(ghost)
        
    def highLightGhost(self,ghost):
        # UP
        if ghost.name == 'clyde' or ghost.name == 'inky':
            self.highLightNodeUp = avg.ImageNode(parent=self.parentNode, opacity=1, angle=math.pi / 2)
            self.highLights.append(self.highLightNodeUp)
            self.highLightNodeUp.setBitmap(self.arrowPic)
            picWidth = self.highLightNodeUp.width
            picHeight = self.highLightNodeUp.height
            highLightNodeUpStartPosition = (ghost.spawnPoint[0] * PPM - picWidth / 2, 0) 
            highLightNodeUpEndPosition = (ghost.spawnPoint[0] * PPM - picWidth / 2, ghost.spawnPoint[1] * PPM - picHeight - ghost.diameter) 
        
            avg.LinearAnim(self.highLightNodeUp, 'pos', 600, highLightNodeUpStartPosition,
                                                    (highLightNodeUpEndPosition[0], highLightNodeUpEndPosition[1] - ghost.diameter)).start()
        # DOWN
        else:
            self.highLightNodeDown = avg.ImageNode(parent=self.parentNode, opacity=1, angle= -math.pi / 2)
            self.highLights.append(self.highLightNodeDown)
            self.highLightNodeDown.setBitmap(self.arrowPic)
            picWidth = self.highLightNodeDown.width
            picHeight = self.highLightNodeDown.height
            highLightNodeDownStartPosition = (ghost.spawnPoint[0] * PPM - picWidth / 2, ghost.parentNode.height)
            highLightNodeDownEndPosition = (ghost.spawnPoint[0] * PPM - picWidth / 2, ghost.spawnPoint[1] * PPM + picHeight) 
    
            avg.LinearAnim(self.highLightNodeDown , 'pos', 600, highLightNodeDownStartPosition,
                                                    highLightNodeDownEndPosition).start()       
        # Clyde
        if ghost.name == 'clyde':
            # UP TEXT 
            self.wordsNodeUp = avg.WordsNode(
                                    parent=self.field2,
                                    pivot=(0, 0),
                                    text=self.highLightText,
                                    wrapmode="wordchar",
                                    font='Comic Sans MS',
                                    color="00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle= -math.pi / 2)
        
            self.highLights.append(self.wordsNodeUp)
            avg.LinearAnim(self.wordsNodeUp, 'pos', 600, (0, -self.wordsNodeUp.width),
                                                    (0, self.wordsNodeUp.width)).start() 
                                                    
            # DOWN TEXT 
            self.wordsNodeDown = avg.WordsNode(
                                    parent=self.field1,
                                    pivot=(0, 0),
                                    text=self.highLightText,
                                    wrapmode="wordchar",
                                    font='Comic Sans MS',
                                    color="00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle=math.pi / 2)
        
            self.highLights.append(self.wordsNodeDown)  
            avg.LinearAnim(self.wordsNodeDown, 'pos', 600, (self.field1.width, self.parentNode.height),
                                                    (self.field1.width, self.parentNode.height - self.wordsNodeDown.width)).start()
                                                    
        g_player.setTimeout(config.ghostTutorial, self.end)

class TetrisTutorial(Tutorial):
    def __init__(self,game):
        Tutorial.__init__(self,game)
        self.highLightText = config.abstractTetrisText
        self.field1 = game.leftPlayer.zone
        self.field2 = game.rightPlayer.zone
        TetrisBar(self.game.display)
        TetrisBar(self.game.display,left = False)
             
    def start(self):  
        # UP TEXT 
        self.wordsNodeUp = avg.WordsNode(
                                    parent=self.field2,
                                    pivot=(0, 0),
                                    text=self.highLightText,
                                    wrapmode="wordchar",
                                    font='Comic Sans MS',
                                    color="00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle= -math.pi / 2)
        
        self.highLights.append(self.wordsNodeUp)
        avg.LinearAnim(self.wordsNodeUp, 'pos', 600, (0, -self.wordsNodeUp.width),
                                                    (0, self.wordsNodeUp.width)).start()                                 
        # DOWN TEXT 
        self.wordsNodeDown = avg.WordsNode(
                                    parent=self.field1,
                                    pivot=(0, 0),
                                    text=self.highLightText,
                                    wrapmode="wordchar",
                                    font='Comic Sans MS',
                                    color="00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle=math.pi / 2)
        
        self.highLights.append(self.wordsNodeDown)  
        avg.LinearAnim(self.wordsNodeDown, 'pos', 600, (self.field1.width, self.parentNode.height),
                                                    (self.field1.width, self.parentNode.height - self.wordsNodeDown.width)).start()
        
        g_player.setTimeout(config.tetrisTutorial, self.end)
                                                    
class BoniTutorial(Tutorial):
    def __init__(self,game):
        Tutorial.__init__(self,game)
        self.highLightText = config.abstractBoniText
        self.field1 = game.leftPlayer.zone
        self.field2 = game.rightPlayer.zone
                
    def start(self):  
        self.wordsNodeUp = avg.WordsNode(
                                    parent=self.field2,
                                    pivot=(0, 0),
                                    text=self.highLightText,
                                    wrapmode="wordchar",
                                    font='Comic Sans MS',
                                    color="00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle= -math.pi / 2)
        
        self.highLights.append(self.wordsNodeUp)
        avg.LinearAnim(self.wordsNodeUp, 'pos', 600, (0, -self.wordsNodeUp.width),
                                                    (0, self.wordsNodeUp.width)).start()                                 
        # DOWN TEXT 
        self.wordsNodeDown = avg.WordsNode(
                                    parent=self.field1,
                                    pivot=(0, 0),
                                    text=self.highLightText,
                                    wrapmode="wordchar",
                                    font='Comic Sans MS',
                                    color="00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle=math.pi / 2)
        
        self.highLights.append(self.wordsNodeDown)  
        avg.LinearAnim(self.wordsNodeDown, 'pos', 600, (self.field1.width, self.parentNode.height),
                                                    (self.field1.width, self.parentNode.height - self.wordsNodeDown.width)).start()
                                                    
        # UP TEXT 
        self.game.bonus = InstantBonus(self.game, ('newBlock', InstantBonus.boni['newBlock'])).setupTutorial(self.wordsNodeUp,self.wordsNodeDown)
        
def killNode(node):
    if node is not None:
        node.active = False
        node.unlink(True)
        node = None
    
def preRenderNOT():
    global displayWidth, displayHeight, brickSize
    chars = '../data/img/char/'
    ballDiameter = 2 * ballRadius * PPM
    TetrisBar.picBlue = avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', (displayWidth / 5, displayHeight))    
    TetrisBar.picGreen = avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', (displayWidth / 5, displayHeight ))
    
    Brick.material = dict(
    GLASS = [avg.SVG(chars+'bat_red.svg', False).renderElement('layer1', (brickSize * PPM, brickSize * PPM)),
                avg.SVG(chars+'bat_red.svg', False).renderElement('layer1', (brickSize * PPM, brickSize * PPM))],
    BUBBLE = [avg.SVG(chars+'bat_red.svg', False).renderElement('layer1', (brickSize * PPM, brickSize * PPM))],
    RUBBER = [avg.SVG(chars+'bat_red.svg', False).renderElement('layer1', (brickSize * PPM, brickSize * PPM)),None])
    # XXX add others?
    
    ballSize = ballDiameter, ballDiameter
    SemipermeableShield.pic = avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', (PPM, displayHeight))
    Ball.pic = avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', ballSize)

    # XXX the mine should look like miss pacman ;)
    Mine.leftPic = avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', ballSize)
    Mine.rightPic = avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', ballSize)
    RedBall.pic = avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', ballSize)
    
    batImgLen = max(1, maxBatSize * PPM / 2)
    batImgWidth = max(1, batImgLen / 10)    
    Bat.blueBat = avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', (batImgWidth, batImgLen))
    Bat.greenBat = avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', (batImgWidth, batImgLen))
    Tower.pic = avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', (2 * ballDiameter, 2 * ballDiameter))
        
    ghostDiameter = 2 * ghostRadius * PPM
    ghostSize = ghostDiameter, ghostDiameter
    Ghost.pics = dict(
        blue=avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', ghostSize),
        blinky=avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', ghostSize),
        inky=avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', ghostSize),
        pinky=avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', ghostSize),
        clyde=avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', ghostSize),
        ghostOfGreen=avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', ghostSize),
        ghostOfBlue=avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', ghostSize))    
    
    boni = chars
    Tutorial.arrowPic = avg.SVG(chars + 'bat_red.svg', False).renderElement('layer1', (displayWidth / 10, displayHeight / 12))
    Rocket.pic = avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', ballSize)

        
    w = (int)(displayWidth / 15)
    bonusSize = w, w
    Bonus.pics = dict(
                invertPac=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize),
                newBlock=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize),
                addOwnGhost=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize),
                hideGhosts=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize),
                
                resetGhosts=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize),
                wave=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize),
                sendGhostsToOtherSide=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize),
                mine=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize),
                pacShot=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize),
                stopGhosts=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize), # TODO fix pic
                flipGhosts=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize),
                tower=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize),
                shield=avg.SVG(boni + 'bat_red.svg', False).renderElement('layer1', bonusSize))

def preRender():
    global displayWidth, displayHeight, brickSize
    chars = '../data/img/char/'
    ballDiameter = 2 * ballRadius * PPM
    TetrisBar.picBlue = avg.SVG(chars + 'tetrisTimeBlue.svg', False).renderElement('layer1', (displayWidth / 5, displayHeight))    
    TetrisBar.picGreen = avg.SVG(chars + 'tetrisTimeGreen.svg', False).renderElement('layer1', (displayWidth / 5, displayHeight))
    
    Brick.material = dict(
    GLASS = [avg.SVG(chars+'glass.svg', False).renderElement('layer1', (brickSize * PPM, brickSize * PPM)),
                avg.SVG(chars+'glass_shat.svg', False).renderElement('layer1', (brickSize * PPM, brickSize * PPM))],
    BUBBLE = [avg.SVG(chars+'bubble.svg', False).renderElement('layer1', (brickSize * PPM, brickSize * PPM))],
    RUBBER = [avg.SVG(chars+'rubber.svg', False).renderElement('layer1', (brickSize * PPM, brickSize * PPM)),None])
    # XXX add others?
    
    ballSize = ballDiameter, ballDiameter
    SemipermeableShield.pic = avg.SVG(chars + 'semiperright.svg', False).renderElement('layer1', (PPM, displayHeight))
    Ball.pic = avg.SVG(chars + 'pacman.svg', False).renderElement('layer1', ballSize)

    # XXX the mine should look like miss pacman ;)
    Mine.leftPic = avg.SVG(chars + 'bluepacman.svg', False).renderElement('layer1', ballSize)
    Mine.rightPic = avg.SVG(chars + 'greenpacman.svg', False).renderElement('layer1', ballSize)
    RedBall.pic = avg.SVG(chars + 'redpacman.svg', False).renderElement('layer1', ballSize)
    
    batImgLen = max(1, maxBatSize * PPM / 2)
    batImgWidth = max(1, batImgLen / 10)    
    Bat.blueBat = avg.SVG(chars + 'bat_blue.svg', False).renderElement('layer1', (batImgWidth, batImgLen))
    Bat.greenBat = avg.SVG(chars + 'bat_green.svg', False).renderElement('layer1', (batImgWidth, batImgLen))
    Tower.pic = avg.SVG(chars + 'tower.svg', False).renderElement('layer1', (2 * ballDiameter, 2 * ballDiameter))
        
    ghostDiameter = 2 * ghostRadius * PPM
    ghostSize = ghostDiameter, ghostDiameter
    
    '''
    better graphics
    Ghost.pics = dict( 
        blue=avg.SVG(chars + 'base.svg', False).renderElement('layer1', ghostSize),
        blinky=avg.SVG(chars + 'borg.svg', False).renderElement('layer1', ghostSize),
        inky=avg.SVG(chars + 'ninja.svg', False).renderElement('layer1', ghostSize),
        pinky=avg.SVG(chars + 'bricky.svg', False).renderElement('layer1', ghostSize),
        clyde=avg.SVG(chars + 'camouflage.svg', False).renderElement('layer1', ghostSize),
        ghostOfGreen=avg.SVG(chars + 'alien.svg', False).renderElement('layer1', ghostSize),
        ghostOfBlue=avg.SVG(chars + 'sunglasser.svg', False).renderElement('layer1', ghostSize))
    '''
    
    Ghost.pics = dict(
        blue=avg.SVG(chars + 'blue.svg', False).renderElement('layer1', ghostSize),
        blinky=avg.SVG(chars + 'blinky.svg', False).renderElement('layer1', ghostSize),
        inky=avg.SVG(chars + 'inky.svg', False).renderElement('layer1', ghostSize),
        pinky=avg.SVG(chars + 'pinky.svg', False).renderElement('layer1', ghostSize),
        clyde=avg.SVG(chars + 'clyde.svg', False).renderElement('layer1', ghostSize),
        ghostOfGreen=avg.SVG(chars + 'ghostOfGreen.svg', False).renderElement('layer1', ghostSize),
        ghostOfBlue=avg.SVG(chars + 'ghostOfBlue.svg', False).renderElement('layer1', ghostSize))    
    
    boni = '../data/img/bonus/' 
    Tutorial.arrowPic = avg.SVG(chars + 'arrow.svg', False).renderElement('layer1', (displayWidth / 10, displayHeight / 12))
    Rocket.pic = avg.SVG(boni + 'wave.svg', False).renderElement('layer1', ballSize)
    w = (int)(displayWidth / 15)
    bonusSize = w, w
    Bonus.pics = dict(
                invertPac=avg.SVG(boni + 'invertPac.svg', False).renderElement('layer1', bonusSize),
                newBlock=avg.SVG(boni + 'newBlock.svg', False).renderElement('layer1', bonusSize),
                addOwnGhost=avg.SVG(boni + 'addOwnGhost.svg', False).renderElement('layer1', bonusSize),
                hideGhosts=avg.SVG(boni + 'hideGhosts.svg', False).renderElement('layer1', bonusSize),
                
                resetGhosts=avg.SVG(boni + 'resetGhosts.svg', False).renderElement('layer1', bonusSize),
                wave=avg.SVG(boni + 'wave.svg', False).renderElement('layer1', bonusSize),
                sendGhostsToOtherSide=avg.SVG(boni + 'sendGhostsToOtherSide.svg', False).renderElement('layer1', bonusSize),
                mine=avg.SVG(boni + 'mine.svg', False).renderElement('layer1', bonusSize),
                pacShot=avg.SVG(boni + 'pacShot.svg', False).renderElement('layer1', bonusSize),
                stopGhosts=avg.SVG(boni + 'stopGhosts.svg', False).renderElement('layer1', bonusSize), # TODO fix pic
                flipGhosts=avg.SVG(boni + 'flipGhosts.svg', False).renderElement('layer1', bonusSize),
                tower=avg.SVG(boni + 'tower.svg', False).renderElement('layer1', bonusSize),
                shield=avg.SVG(boni + 'shield.svg', False).renderElement('layer1', bonusSize))