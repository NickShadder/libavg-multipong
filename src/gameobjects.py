'''
Created on 15.02.2012

@author: 2526240
'''

import random
import math

from libavg import avg, ui
from Box2D import b2EdgeShape, b2PolygonShape, b2FixtureDef, b2CircleShape, b2Filter, b2Vec2

from config import PPM, pointsToWin, ballRadius, ghostRadius, brickSize, maxBatSize, bonusTime, brickLines

cats = {'border':0x0001, 'ghost':0x0002, 'ball':0x0004, 'brick':0x0008, 'redball':0x0010, 'semiborder':0x0020, 'ownball':0x0040,'bat':0x0080}
def dontCollideWith(*categories): return reduce(lambda x, y: x ^ y, [cats[el] for el in categories], 0xFFFF)

standardXInertia = 20 * ballRadius # XXX solve more elegantly
g_player = avg.Player.get()
halfBrickSize = brickSize / 2
displayWidth = displayHeight = bricksPerLine = None 

class Player:
    def __init__(self, game, avgNode):
        self.points = 0
        self.other = None
        self.game = game
        self.zone = avgNode
        self.left = avgNode.pos == (0, 0)
        avgNode.player = self # monkey patch
        left = avgNode.pos == (0, 0)
        angle = math.pi / 2 if left else -math.pi / 2
        pos = (avgNode.width, 2) if left else (0, avgNode.height - 2)            
        # XXX gameobects may obstruct view of the points!
        self.pointsDisplay = avg.WordsNode(parent=avgNode, pivot=(0, 0), pos=pos, angle=angle,
                                           text='Points: 0 / %d' % pointsToWin)
        self.raster = [[None for x in xrange(bricksPerLine)] for y in xrange(brickLines)]
        self.nodeRaster = []                    #rectNodes to display the margins of the raster
        pixelBrickSize = brickSize * PPM
        for x in xrange(brickLines):
            for y in xrange(bricksPerLine):
                xPos, yPos = x * pixelBrickSize, y * pixelBrickSize
                if not left:
                    xPos = avgNode.size[0] - xPos - pixelBrickSize
                self.nodeRaster.append(avg.RectNode(parent=avgNode, pos=(xPos, yPos), size=(pixelBrickSize, pixelBrickSize), active=False))
    
    def isLeft(self):
        return self.left
    
    def addPoint(self, points=1):
        self.points += points
        self.updateDisplay()
        if self.points >= pointsToWin:
            self.game.win(self)

    def removePoint(self, points=1):
        self.points = max(0, self.points - points)
        self.updateDisplay()
    
    def updateDisplay(self):
        self.pointsDisplay.text = 'Points: %d / %d' % (self.points, pointsToWin)

    def nextFreeBrick(self):
        # TODO this is very ugly and slow - better keep a list of available bricks
        for x in xrange(brickLines):
            for y in xrange(bricksPerLine):
                brick = self.raster[x][y]
                if brick is not None:
                    if brick.getBonus() is None:
                        return brick
        return None
    
    def addBonus(self, bonus):
        brick = self.nextFreeBrick()
        if brick is not None:
            brick.setBonus(bonus)
            bonus.saveBonus(brick)

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
    hightLightpic = None
    def __init__(self, game, renderer, world, parentNode, position):
        GameObject.__init__(self, renderer, world)
        self.game = game
        self.parentNode = parentNode
        self.spawnPoint = parentNode.pivot / PPM # XXX maybe make a static class variable
        self.leftPlayer = game.leftPlayer
        self.rightPlayer = game.rightPlayer
        self.lastPlayer = None
        self.diameter =  2 * ballRadius * PPM
        self.node = avg.ImageNode(parent=parentNode)
        self.node.setBitmap(Ball.pic)
        self.body = world.CreateDynamicBody(position=position, userData=self, active=False, bullet=True) # XXX reevaluate bullet-ness
        self.body.CreateCircleFixture(radius=ballRadius, density=1, restitution=.3,
                                      friction=.01, groupIndex=1, categoryBits=cats['ball'],
                                      maskBits=dontCollideWith('ghost'), userData='ball')

        self.body.CreateCircleFixture(radius=ballRadius, userData='ball', isSensor=True)
        self.nextDir = (random.choice([standardXInertia, -standardXInertia]), random.randint(-10, 10))
        self.__appear(lambda:self.nudge())
        
    def highLight(self):
        self.highLightText = "Hier wird der Spielball (auch Pacman genannt) erscheinen.<br/>" +"Erreicht er deinen Rand, bekommt der Gegner einen Punkt.<br/>" + "Mit deinem Schlaeger kannst du dies verhindern.<br/>" + "Platziere an zwei Stellen einen Finger, um den Schlaeger zu erzeugen.<br/>" + "Versuche es."         
        self.highLights = []
        # UP
        self.highLightNodeUp = avg.ImageNode(parent=self.parentNode, opacity=1,angle = math.pi/2)
        self.highLights.append(self.highLightNodeUp)
        self.highLightNodeUp.setBitmap(self.hightLightpic)
        picWidth = self.highLightNodeUp.size[0]
        picHeight = self.highLightNodeUp.size[1]
        highLightNodeUpStartPosition = (self.spawnPoint[0]*PPM - picWidth/2,0) 
        highLightNodeUpEndPosition = (self.spawnPoint[0]*PPM - picWidth/2,self.spawnPoint[1]*PPM - picHeight - self.diameter) 
        
        avg.LinearAnim(self.highLightNodeUp, 'pos', 600,highLightNodeUpStartPosition, 
                                                    highLightNodeUpEndPosition).start()
        # UP TEXT 
        self.wordsNodeUp = avg.WordsNode(
                                    parent=self.rightPlayer.zone, 
                                    pivot=(0, 0),
                                    text=self.highLightText, 
                                    wrapmode="wordchar", 
                                    font= 'Comic Sans MS', 
                                    color = "00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle = -math.pi/2)
        
        self.highLights.append(self.wordsNodeUp)
        avg.LinearAnim(self.wordsNodeUp, 'pos', 600,(0,-self.wordsNodeUp.width), 
                                                    (0,self.wordsNodeUp.width)).start() 
                                                                    
        # DOWN
        self.highLightNodeDown = avg.ImageNode(parent=self.parentNode, opacity=1,angle = -math.pi/2)
        self.highLights.append(self.highLightNodeDown)
        self.highLightNodeDown.setBitmap(self.hightLightpic)
        highLightNodeDownStartPosition = (self.spawnPoint[0]*PPM - picWidth/2,self.parentNode.size[1])
        highLightNodeDownEndPosition = (self.spawnPoint[0]*PPM - picWidth/2, self.spawnPoint[1]*PPM + picHeight) 
        
        
        avg.LinearAnim(self.highLightNodeDown , 'pos', 600,highLightNodeDownStartPosition, 
                                                    highLightNodeDownEndPosition).start()     
        
        # DOWN TEXT 
        self.wordsNodeDown = avg.WordsNode(
                                    parent=self.leftPlayer.zone, 
                                    pivot=(0, 0),
                                    text=self.highLightText, 
                                    wrapmode="wordchar", 
                                    font= 'Comic Sans MS', 
                                    color = "00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle = math.pi/2)
        
        self.highLights.append(self.wordsNodeDown)  
        avg.LinearAnim(self.wordsNodeDown, 'pos', 600,(self.leftPlayer.zone.width,self.parentNode.size[1]), 
                                                    (self.leftPlayer.zone.width,self.parentNode.size[1] - self.wordsNodeDown.width)).start()        
        
                                                                                                                                   
        g_player.setTimeout(20000, self.dehighLight)
    
    def dehighLight(self):
        for node in self.highLights:
            node.active = False
            node.unlink(True)
            node = None  
            
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
        # XXX I'm sure there is a better way to do this
        lz, rz = self.leftPlayer.zone, self.rightPlayer.zone
        if lz.getAbsPos((0, 0))[0] < self.node.pos[0] < lz.getAbsPos(lz.size)[0]:
            return self.leftPlayer
        elif rz.getAbsPos((0, 0))[0] < self.node.pos[0] < rz.getAbsPos(rz.size)[0]:
            return self.rightPlayer
        else:
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

class Mine(Ball):
    leftPic = rightPic = None
    def __init__(self, game, parentNode, owner):
        position = (random.randint(0,(int)(parentNode.size[0]/PPM)),random.randint(0,(int)(parentNode.size[1]/PPM)))
        Ball.__init__(self, game, game.renderer, game.world, parentNode,position)
        self.owner = owner
        self.node.setBitmap(Mine.leftPic if owner.isLeft() else Mine.rightPic)
        self.body.active=True
        self.body.userData = self
        filterdef = b2Filter(groupIndex = -1,categoryBits = cats['ownball'],maskBits = dontCollideWith('ghost','ball','bat'))        
        for fix in self.body.fixtures:
            fix.userData = 'ownball'
            fix.filterData = filterdef
        # TODO the mine shouldn't live forever, should it?
            
    def getOwner(self):
        return self.owner

    # Override
    def nudge(self, direction=None):
        pass
            
class RedBall(Ball):
    pic = None
    def __init__(self, game, parentNode, position,left):
        Ball.__init__(self, game, game.renderer, game.world, parentNode, position)
        self.node.setBitmap(RedBall.pic)
        self.left = left
        self.body.userData = self
        filterdef = b2Filter(groupIndex = -1,categoryBits = cats['redball'],maskBits = dontCollideWith('ball','redball','ownball'))
        for fix in self.body.fixtures:
            fix.userData = 'redball'
            fix.filterData = filterdef        
    # Override
    def nudge(self, direction=None):
        self.body.active = True
        speedX = -25 # XXX tweak
        if self.left:
            speedX = -speedX
        self.body.linearVelocity = (speedX, random.randint(-10,10))
              
    def hit(self):
        self.destroy()

class GhostBall:
    def __init__(self, parentNode, y, left):
        diameter =  2 * ballRadius * PPM
        self.node = avg.ImageNode(parent=parentNode, size=(diameter, diameter))
        self.node.setBitmap(Ball.pic)
        width = int(parentNode.size[0])
        start = -diameter,y
        end = width,y
        if not left: 
            start,end = end,start
            self.node.angle = math.pi
        avg.LinearAnim(self.node, 'pos', width, start, end, False, None, self.destroy).start()                 
        
    def destroy(self):
        if self.node is not None:
            self.node.active = False
            self.node.unlink(True)
            self.node = None   

class Cloud:    
    pic = None    
    def __init__(self, parentNode):
        self.parentNode = parentNode
        self.node = avg.ImageNode(parent=parentNode, opacity=1, pos=(0, 0))
        self.node.setBitmap(Cloud.pic)
        # TODO this can't be it, surely there is more to this than I can see right now...
                
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
            self.node.angle=math.pi
            x = displayThird
        self.node.pos = x,0
        self.node.setBitmap(SemipermeableShield.pic)
        
        self.body = self.world.CreateStaticBody(position=(x/PPM+.5, displayHeight/(2*PPM)), userData=self)
        self.body.CreateFixture(shape=b2PolygonShape(box=(.5, displayHeight/(2*PPM), (0, 0), math.pi)), density=1,
                                restitution=1, groupIndex = -2, categoryBits=cats['semiborder'], userData='semiborder', 
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

    hightLightpic = None
    pics = None    

    def __init__(self, renderer, world, parentNode, position, name, owner=None, mortal=1):
        GameObject.__init__(self, renderer, world)
        self.parentNode = parentNode
        self.spawnPoint = position
        self.name = name
        self.diameter = 2 * ballRadius * PPM
        self.trend = None
        self.owner = owner
        self.mortal = mortal
        self.node = avg.ImageNode(parent=parentNode, opacity=.85)
        # self.setShadow('ADD8E6')
        ghostUpper = b2FixtureDef(userData='ghost', shape=b2CircleShape(radius=ghostRadius),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'], maskBits=dontCollideWith('ball'))
        ghostLower = b2FixtureDef(userData='ghost', shape=b2PolygonShape(box=(ghostRadius, ghostRadius / 2, (0, -ghostRadius / 2), 0)),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'], maskBits=dontCollideWith('ball'))
        self.body = world.CreateDynamicBody(position=position, fixtures=[ghostUpper, ghostLower],
                                            userData=self, fixedRotation=True)
        self.changeMortality()
        self.render()
        self.move()
        
    def highLight(self,field1,field2):         
        self.highLights = []
        self.highLightText = "Dies sind Geister. Sind kommen immer dort wo die Pfeile sind.<br/>" + "Clyde, Inky, Pinky und Blinky.<br/>" + "Ist ein Geist nicht blau, frisst er den Pacman.<br/>" + "Der Spieler, der den Pacman als letztes mit seinem Schlaeger beruehrt hat, verliert dabei einen Punkt.<br/>" + "Ist ein Geist blau, frisst der Pacman den Geist.<br/>" + "Der Spieler, der den Pacman als letztes mit seinem Schlaeger beruehrt hat, bekommt dabei einen Punkt." 
        # UP
        if self.name == 'clyde' or self.name == 'inky':
            self.highLightNodeUp = avg.ImageNode(parent=self.parentNode, opacity=1,angle = math.pi/2)
            self.highLights.append(self.highLightNodeUp)
            self.highLightNodeUp.setBitmap(self.hightLightpic)
            picWidth = self.highLightNodeUp.size[0]
            picHeight = self.highLightNodeUp.size[1]
            highLightNodeUpStartPosition = (self.spawnPoint[0]*PPM - picWidth/2,0) 
            highLightNodeUpEndPosition = (self.spawnPoint[0]*PPM - picWidth/2,self.spawnPoint[1]*PPM - picHeight - self.diameter) 
        
            avg.LinearAnim(self.highLightNodeUp, 'pos', 600,highLightNodeUpStartPosition, 
                                                    (highLightNodeUpEndPosition[0],highLightNodeUpEndPosition[1]-self.diameter)).start()
        # DOWN
        else:
            self.highLightNodeDown = avg.ImageNode(parent=self.parentNode, opacity=1,angle = -math.pi/2)
            self.highLights.append(self.highLightNodeDown)
            self.highLightNodeDown.setBitmap(self.hightLightpic)
            picWidth = self.highLightNodeDown.size[0]
            picHeight = self.highLightNodeDown.size[1]
            highLightNodeDownStartPosition = (self.spawnPoint[0]*PPM - picWidth/2,self.parentNode.size[1])
            highLightNodeDownEndPosition = (self.spawnPoint[0]*PPM - picWidth/2, self.spawnPoint[1]*PPM + picHeight) 
    
            avg.LinearAnim(self.highLightNodeDown , 'pos', 600,highLightNodeDownStartPosition, 
                                                    highLightNodeDownEndPosition).start()       
        # Clyde
        if self.name == 'clyde':
            # UP TEXT 
            self.wordsNodeUp = avg.WordsNode(
                                    parent=field2, 
                                    pivot=(0, 0),
                                    text=self.highLightText, 
                                    wrapmode="wordchar", 
                                    font= 'Comic Sans MS', 
                                    color = "00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle = -math.pi/2)
        
            self.highLights.append(self.wordsNodeUp)
            avg.LinearAnim(self.wordsNodeUp, 'pos', 600,(0,-self.wordsNodeUp.width), 
                                                    (0,self.wordsNodeUp.width)).start() 
                                                    
            # DOWN TEXT 
            self.wordsNodeDown = avg.WordsNode(
                                    parent=field1, 
                                    pivot=(0, 0),
                                    text=self.highLightText, 
                                    wrapmode="wordchar", 
                                    font= 'Comic Sans MS', 
                                    color = "00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle = math.pi/2)
        
            self.highLights.append(self.wordsNodeDown)  
            avg.LinearAnim(self.wordsNodeDown, 'pos', 600,(field1.width,self.parentNode.size[1]), 
                                                    (field1.width,self.parentNode.size[1] - self.wordsNodeDown.width)).start()
                    
        
        g_player.setTimeout(20000, self.dehighLight)
    
    def dehighLight(self):
        for node in self.highLights:
            node.active = False
            node.unlink(True)
            node = None  
        self.destroy()
    
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
            self.mortal = 0 # ghost respawns in immortal state XXX rerender this?
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
        self.trend = trend
    
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

                                
class BorderLine:
    body = None
    def __init__(self, world, pos1, pos2, restitution=0, sensor=False, *noCollisions):
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

class Tower:
    pic = None
    def __init__(self, game, position, number, left=False):
        self.game = game
        self.left = left
        self.firing = None
        self.node = avg.ImageNode(parent=game.display,pos=position)
        game.display.reorderChild(self.node,5) 
        self.node.setBitmap(Tower.pic)
        ballOffset = ballRadius,2*ballRadius
        self.firingpos = (b2Vec2(position)+self.node.size)/PPM-ballOffset
        if left:
            self.node.angle = math.pi
            self.firingpos = b2Vec2(position)/PPM+ballOffset
            
        g_player.setTimeout(1000 + (number * 1000), self.fire)
        g_player.setTimeout(30000 + (number * 1000), self.destroy)
            
    def fire(self):
        if self.node is not None:
            self.game.getRedBalls().append(RedBall(self.game,self.game.display, self.firingpos,self.left))
            self.firing = g_player.setTimeout(3000, self.fire)
        
    def destroy(self):
        if self.node is not None:
            self.node.active = False
            self.node.unlink(True)
            self.node = None
        if self.firing is not None:
            g_player.clearInterval(self.firing)

class Bonus:    
    pics = None
    hightLightpic = None
    def __init__(self, game, (name, effect)):
        parentNode = game.display
        self.highLights = []   
        displayWidth = parentNode.size[0]
        displayHeight = parentNode.size[1]
        self.name = name 
        self.size = (displayWidth / 15, parentNode.size[0] / 15)
        self.pic = Bonus.pics[name]
        self.parentNode, self.game, self.world = parentNode, game, game.world
        self.effect = effect
        self.leftBonus = avg.ImageNode(parent=parentNode, pos=(displayWidth / 3, displayHeight / 2 - (self.size[1] / 2)))
        self.leftBonus.setBitmap(self.pic)
        
        self.rightBonus = avg.ImageNode(parent=parentNode, pos=(2 * displayWidth / 3 - self.size[0], displayHeight / 2 - (self.size[1] / 2)))
        self.rightBonus.setBitmap(self.pic)
        self.leftBonus.setEventHandler(avg.CURSORDOWN, avg.TOUCH, self.onClick)
        self.rightBonus.setEventHandler(avg.CURSORDOWN, avg.TOUCH, self.onClick)
        self.timeout = g_player.setTimeout(bonusTime * 1000, self.vanish)

    def highLight(self,field1,field2):
        # UP
        self.highLightNodeUp = avg.ImageNode(parent=self.parentNode, opacity=1,angle = math.pi/2)
        self.highLights.append(self.highLightNodeUp)
        self.highLightNodeUp.setBitmap(self.hightLightpic)
        highLightNodeUpStartPosition = (self.rightBonus.pos[0],0) 
        highLightNodeUpEndPosition = (self.rightBonus.pos[0],self.rightBonus.pos[1] - self.rightBonus.size[1]) 
        
        avg.LinearAnim(self.highLightNodeUp, 'pos', 600,highLightNodeUpStartPosition, 
                                                    highLightNodeUpEndPosition).start()
        
        # DOWN
        self.highLightNodeDown = avg.ImageNode(parent=self.parentNode, opacity=1,angle = -math.pi/2)
        self.highLights.append(self.highLightNodeDown)
        self.highLightNodeDown.setBitmap(self.hightLightpic)
        highLightNodeDownStartPosition = (self.leftBonus.pos[0],self.parentNode.size[1])
        highLightNodeDownEndPosition = (self.leftBonus.pos[0], self.leftBonus.pos[1] + self.leftBonus.size[1]) 
    
        avg.LinearAnim(self.highLightNodeDown , 'pos', 600,highLightNodeDownStartPosition, 
                                                    highLightNodeDownEndPosition).start()
                                                    
        self.highLightText = "Bonusbeschreibung Line1<br/>" + "Bla Bla<br/>" + "Bla Bla2br/>" + "Bla Bla3<br/>"                                                     
        
        # UP TEXT 
        self.wordsNodeUp = avg.WordsNode(
                                    parent=field2, 
                                    pivot=(0, 0),
                                    text=self.highLightText, 
                                    wrapmode="wordchar", 
                                    font= 'Comic Sans MS', 
                                    color = "00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle = -math.pi/2)
        
        self.highLights.append(self.wordsNodeUp)
        avg.LinearAnim(self.wordsNodeUp, 'pos', 600,(0,-self.wordsNodeUp.width), 
                                                    (0,self.wordsNodeUp.width)).start() 
                                                    
            # DOWN TEXT 
        self.wordsNodeDown = avg.WordsNode(
                                    parent=field1, 
                                    pivot=(0, 0),
                                    text=self.highLightText, 
                                    wrapmode="wordchar", 
                                    font= 'Comic Sans MS', 
                                    color = "00FF00",
                                    fontsize=15,
                                    variant="bold",
                                    angle = math.pi/2)
        
        self.highLights.append(self.wordsNodeDown)  
        avg.LinearAnim(self.wordsNodeDown, 'pos', 600,(field1.width,self.parentNode.size[1]), 
                                                    (field1.width,self.parentNode.size[1] - self.wordsNodeDown.width)).start()                                                        
        # g_player.setTimeout(20000, self.dehighLight)
    
    def dehighLight(self):
        for node in self.highLights:
            node.active = False
            node.unlink(True)
            node = None  
        
    def onClick(self, event):
        g_player.clearInterval(self.timeout)
        res = event.node == self.leftBonus
        self.vanish()
        return res

    def vanish(self):
        self.dehighLight()
        if self.leftBonus is not None:
            self.leftBonus.active = False
            self.leftBonus.unlink(True)
            self.leftBonus = None
        if self.rightBonus is not None:
            self.rightBonus.active = False
            self.rightBonus.unlink(True)
            self.rightBonus = None
        
    def applyEffect(self, player):
        self.effect(self, player)
    
    def saveBonus(self, brick):
        hSize = brickSize * PPM / 2
        position = hSize / 2
        self.__node = avg.ImageNode(parent = brick.getDivNode(), pos = (position, position), size = (hSize, hSize))
        self.__node.setBitmap(self.pic)
        self.__node.setEventHandler(avg.CURSORDOWN, avg.TOUCH, lambda e,brick=brick: self.__useBonus(brick))
    
    def destroy(self, brick):
        brick.removeBonus()
        self.__node.active = False # XXX animate?
        self.__node.unlink(True)        
    
    def __useBonus(self, brick):
        self.destroy(brick)
        self.applyEffect(brick.getPlayer())
        #brick.getPlayer.moveTogetherBoni()        XXX
        
    def pacShot(self, player):
        height = self.parentNode.size[1]
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
        
    def bringBackGhosts(self, player=None):
        self.hideGhosts(player) # kill off ghosts created by the players
        self.game.createGhosts() # restore the original four ghosts 
         
    def addGhost(self, player):        
        if player.isLeft():
            name = "blue2"
        else:
            name = "green"            
        self.game.ghosts.append(Ghost(self.game.renderer, self.world, self.parentNode, self.game.middle - (0, (ballRadius + ghostRadius) * 2), name, player))
        
    def sendGhostsToOpponent(self, player):
        for g in self.game.getGhosts():
            if player.isLeft():
                g.setTrend('right')
            else:
                g.setTrend('left')
                                  
    def setTowers(self, player):
        thirdWidth = self.parentNode.width/3
        quarterHeight = self.parentNode.height/4
        if player.isLeft():
            x = thirdWidth - 4*ballRadius*PPM
        else:
            x = 2*thirdWidth
        for i in range(1,4):
            Tower(self.game, (x,i*quarterHeight), i, player.isLeft())        
            
    def newOwnBall(self, player=None):
        Mine(self.game, self.parentNode, player)
          
    def newBlock(self, player): 
        height = (self.parentNode.size[1] / 2) - (brickSize * PPM)
        
        width = self.parentNode.size[0]
        if player.isLeft():
            Block(self.game.display, self.game.renderer, self.world, (width / 3 - (brickSize * 5 * PPM), height), (self.game.leftPlayer, self.game.rightPlayer), random.choice(Block.form.values()))
        else:
            Block(self.game.display, self.game.renderer, self.world, (2 * width / 3, height), (self.game.leftPlayer, self.game.rightPlayer), random.choice(Block.form.values()))
            
    def buildShield(self, player):
        s = SemipermeableShield(self.game, player.isLeft(),'ghost')
        g_player.setTimeout(10000, s.destroy) # XXX tweak time
     
class PersistentBonus(Bonus):
    boni = dict(
                pacShot=Bonus.pacShot,
                stopGhosts=Bonus.stopGhosts,
                flipGhosts=Bonus.flipGhostStates,
                wheel=Bonus.setTowers,
                onlyPong=Bonus.buildShield,
                pacman=Bonus.newOwnBall
                )
    
    def __init__(self, game, (name, effect)):
        Bonus.__init__(self, game, (name, effect))
    
    def onClick(self, event):
        (self.game.leftPlayer if Bonus.onClick(self, event) else self.game.rightPlayer).addBonus(self)  
        
class InstantBonus(Bonus):
    boni = dict(
                invertPac=Bonus.invertPac,
                newBlock=Bonus.newBlock,
                addClyde=Bonus.addGhost,
                Bonus4=Bonus.hideGhosts,
                Bonus5=Bonus.bringBackGhosts,
                Bonus6=Bonus.sendGhostsToOpponent,
                pacman=Bonus.newOwnBall
                )

          
    def __init__(self, game, (name, effect)):
        Bonus.__init__(self, game, (name, effect))
        
    def onClick(self, event):
        self.applyEffect(self.game.leftPlayer if Bonus.onClick(self, event) else self.game.rightPlayer)
        
'''
class Pill:
    # TODO refactor as Pill(BallBonus) or kill completely
    def __init__(self, parentNode, game, world, position, radius=.5):
        self.node = avg.CircleNode(parent=parentNode, fillopacity=1, fillcolor="FFFF00", color='000000')
        d = {'type':'body', 'node':self.node}
        self.world = world
        self.game = game
        self.body = world.CreateDynamicBody(position=position, userData=d)
        self.body.CreateCircleFixture(radius=radius, density=1, friction=1, restitution=1)
        self.body.bullet = True # seriously?
'''
            
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
                                  categoryBits = cats['bat'])
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
    RUBBER = 2, [avg.SVG('../data/img/char/rubber.svg',False).renderElement('layer1', (brickSize * PPM, brickSize * PPM))] # XXX make unkillable?
    # TODO add others

class Brick(GameObject):
    def __init__(self, parentBlock, renderer, world, parentNode, pos, mat=None):
        GameObject.__init__(self, renderer, world)
        self.block, self.hitcount, self.material = parentBlock, 0, mat
        self.parentNode = parentNode
        if self.material is None:
            self.material = random.choice(filter(lambda x:type(x).__name__ == 'tuple', Material.__dict__.values())) # XXX hacky
        self.node = avg.ImageNode(parent=parentBlock.container, pos=pos)
        self.node.setBitmap(self.material[1][0])
        self.__divNode = None
        self.__index = None
        self.__bonus = None

    # spawn a physical object
    def materialize(self, onLeft, x, y, pos=None):
        if pos is None:
            pos = (self.node.pos + self.node.pivot) / PPM # TODO this looks like trouble
        self.node.unlink()
        self.parentNode.appendChild(self.node)
        self.__divNode = avg.DivNode(parent = self.parentNode, pos = self.node.pos, size = self.node.size)
        fixtureDef = b2FixtureDef (userData='brick', shape=b2PolygonShape (box=(halfBrickSize, halfBrickSize)),
                                  density=1, friction=.03, restitution=1, categoryBits=cats['brick'])
        self.body = self.world.CreateStaticBody(position=pos, userData=self)
        self.body.CreateFixture(fixtureDef)
        self.__index = (x, y)
    
    def hit(self):
        self.hitcount += 1
        if self.hitcount < len(self.material[1]):
            self.node.setBitmap(self.material[1][self.hitcount])
        else:
            self.block.getPlayer().raster[self.__index[0]][self.__index[1]] = None
            if self.__bonus is not None:
                self.__bonus.destroy(self)
            self.destroy() # XXX maybe override destroy for special effects, or call something like vanish first
    
    def getBonus(self):
        return self.__bonus
    
    def setBonus(self, bonus):
        self.__bonus = bonus
    
    def removeBonus(self):
        self.__bonus = None
    
    def getDivNode(self):
        return self.__divNode
    
    def getPlayer(self):
        return self.block.getPlayer()

    def render(self):
        pass # XXX move the empty method to GameObject when the game is ready

    # override
    def destroy(self):
        GameObject.destroy(self)
        if self.__divNode is not None:
            self.__divNode.unlink(True)
    
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
    TPIECE=(4, 3, 1)
)
    def __init__(self, parentNode, renderer, world, position, player, form=None, flip=False, material=None, angle=0):        
        self.parentNode, self.renderer, self.world, self.position = parentNode, renderer, world, position
        self.form, self.flip, self.material, self.angle = form, flip, material, angle
        self.leftPlayer, self.rightPlayer = player
        if form is None:
            self.form = random.choice(Block.form.values())
        self.brickList = []
        self.container = avg.DivNode(parent=parentNode, pos=position, angle=angle)
        # XXX maybe set pivot
        brickSizeInPx = brickSize * PPM
        bricks, maxLineLength, offset = self.form
        rightMostPos = (maxLineLength - 1) * brickSizeInPx
        line = -1
        for b in range(bricks):
            posInLine = b % maxLineLength
            if posInLine == 0: line += 1
            posX = (line * offset + posInLine) * brickSizeInPx
            if flip: posX = rightMostPos - posX
            posY = line * brickSizeInPx
            self.brickList.append(Brick(self, renderer, world, parentNode, (posX, posY), material))
        self.onLeft = False
        self.__alive = False
        self.__assigned = False
        self.__timeCall = g_player.setTimeout(3000, self.__vanish)
        self.__cursor1 = None
        self.__cursor2 = None
        self.container.setEventHandler(avg.CURSORDOWN, avg.TOUCH, self.__cursorReg)
        self.container.setEventHandler(avg.CURSOROUT, avg.TOUCH, self.__cursorDeReg)
        ui.DragRecognizer(self.container, moveHandler=self.__onMove, coordSysNode = self.brickList[0].node)
        ui.TransformRecognizer(self.container, moveHandler=self.__onTransform, endHandler=self.__moveEnd)
    
    def __onMove(self, e, offset):
        if self.__cursor2 is None:
            if self.__timeCall is not None:
                g_player.clearInterval(self.__timeCall)
                self.__timeCall = None
            self.container.pos += offset
            widthDisplay = self.parentNode.size[1] # XXX this calculation should be outside the handler
            widthThird = widthDisplay / 3
            if self.__assigned:
                self.__testInsertion()
            else:
                if e.pos[0] < widthThird:
                    self.__assigned = True
                    self.onLeft = True
                    self.__displayRaster(True)
                elif e.pos[0] > widthDisplay - widthThird:
                    self.__assigned = True
                    self.__displayRaster(True)
                else:
                    self.__colourRed()
    
    def __cursorReg(self, event):
        if self.__cursor1 is None:
            self.__cursor1 = event.cursorid
        else:
            self.__cursor2 = event.cursorid
    
    def __cursorDeReg(self, event):
        if self.__cursor2 is event.cursorid:
            self.__cursor2 = None
        else:
            self.__cursor1 = self.__cursor2
            self.__cursor2 = None
    
    def __onTransform(self, tr):
        if self.__timeCall is not None:
            g_player.clearInterval(self.__timeCall)
            self.__timeCall = None
#        if self.__cursor2 is None:
#            # only one touch -> no intent to rotate -> move
#            self.container.pos += tr.trans
#            widthDisplay = self.parentNode.size[1]
#            widthThird = widthDisplay / 3
#            for b in self.brickList:
#                if self.__assigned:
#                    break
#                else:
#                    if b.node.pos[0] + self.container.pos[0] < widthThird:
#                        self.__assigned = True
#                        self.onLeft = True
#                        self.__displayRaster(True)        
#                    elif b.node.pos[0] + self.container.pos[0] > widthDisplay - widthThird - brickSize * PPM:
#                        self.__assigned = True
#                        self.__displayRaster(True)
#            if self.__assigned:
#                self.__testInsertion()
#            else:
#                self.__colourRed()
#        else:
        if self.__cursor2 is not None:
            self.container.angle += tr.rot
    
    def __testInsertion(self):
        possible = True        
        testRaster = (self.leftPlayer if self.onLeft else self.rightPlayer).raster        
        for b in self.brickList:
            (x, y) = self.__calculateIndices(b.node.pos)
            if ((x >= brickLines) or (y >= bricksPerLine) or
                (x < 0) or (y < 0) or 
                (testRaster[x][y] is not None)):
                possible = False
                break
        if possible:
            self.__colourGreen()
        else:
            self.__colourRed()
    
    def __calculateIndices(self, position):
        pixelBrickSize = brickSize * PPM
        if self.onLeft:
            x = int(round((position[0] + self.container.pos[0]) / pixelBrickSize))
        else:
            x = int(round((self.parentNode.size[0] - position[0] - self.container.pos[0] - pixelBrickSize) / pixelBrickSize))
        y = int(round((position[1] + self.container.pos[1]) / pixelBrickSize))
#        if y >= bricksPerLine:
#            y = bricksPerLine - 1
#        elif y < 0:
#            y = 0
#        if x < 0:
#            x = 0        
        return (x, y)
    
    def __colourRed(self):
        for b in self.brickList:
            b.node.intensity = (1, 0, 0)
            self.__alive = False
    
    def __colourGreen(self):
        for b in self.brickList:
            b.node.intensity = (0, 1, 0)
            self.__alive = True
    
    def __vanish(self):
        for b in self.brickList:
            if b.node is not None:
                b.node.active = False
                b.node.unlink(True)
                b.node = None
        if self.container is not None:
            self.container.unlink(True)
        self.__displayRaster(False)
        if self.__timeCall is not None:
            g_player.clearInterval(self.__timeCall)
            self.__timeCall = None
    
    def __moveEnd(self, tr):
        self.container.angle = round(2 * self.container.angle / math.pi) * math.pi / 2
        pixelBrickSize = brickSize * PPM
        if not self.__alive:
            self.__timeCall = g_player.setTimeout(1000, self.__vanish)
        else:
            for b in self.brickList:
                b.node.intensity = (1, 1, 1)
                (x, y) = self.__calculateIndices(b.node.pos)
                xPos, yPos = x * pixelBrickSize, y * pixelBrickSize
                if self.onLeft:
                    self.leftPlayer.raster[x][y] = b
                else:
                    xPos = self.parentNode.size[0] - xPos - pixelBrickSize
                    self.rightPlayer.raster[x][y] = b
                b.node.pos = (xPos, yPos)
                b.node.sensitive = False
                b.materialize(self.onLeft, x, y)
            self.container.active = False
            self.container.unlink(True)
            self.__displayRaster(False)
    
    def __displayRaster(self, on):
        if self.onLeft:
            raster = self.leftPlayer.nodeRaster
        else:
            raster = self.rightPlayer.nodeRaster
        for n in raster:
            n.active = on        
    
    def getPlayer(self):
        if self.onLeft:
            return self.leftPlayer
        return self.rightPlayer


def preRender():
    global displayWidth, displayHeight
    chars = '../data/img/char/'
    ballDiameter = 2 * ballRadius * PPM
    ballSize = ballDiameter,ballDiameter
    SemipermeableShield.pic = avg.SVG(chars+'semiperright.svg', False).renderElement('layer1', (PPM, displayHeight))
    Ball.pic = avg.SVG(chars+'pacman.svg', False).renderElement('layer1', ballSize)
    # XXX the mine should look like miss pacman ;)
    Mine.leftPic = avg.SVG(chars+'bluepacman.svg', False).renderElement('layer1', ballSize)
    Mine.rightPic = avg.SVG(chars+'greenpacman.svg', False).renderElement('layer1', ballSize)
    RedBall.pic = avg.SVG(chars+'redpacman.svg', False).renderElement('layer1', ballSize)
    Cloud.pic = avg.SVG(chars+'cloud.svg', False).renderElement('layer1', (500, 1000)) # XXX remove hardcode
    Tower.pic = avg.SVG(chars+'tower.svg', False).renderElement('layer1', (2*ballDiameter,2*ballDiameter)) # XXX remove hardcode
    
    batImgLen = max(1, maxBatSize * PPM / 2)
    batImgWidth = max(1, batImgLen / 10)    
    Bat.blueBat = avg.SVG(chars+'bat_blue.svg', False).renderElement('layer1', (batImgWidth, batImgLen))
    Bat.greenBat = avg.SVG(chars+'bat_green.svg', False).renderElement('layer1', (batImgWidth, batImgLen))
    
    ghostDiameter = 2 * ghostRadius * PPM
    ghostSize = ghostDiameter,ghostDiameter
    Ghost.pics = dict(
        blue = avg.SVG(chars+'blue.svg', False).renderElement('layer1', ghostSize),
        blinky = avg.SVG(chars+'blinky.svg', False).renderElement('layer1', ghostSize),
        inky = avg.SVG(chars+'inky.svg', False).renderElement('layer1', ghostSize),
        pinky = avg.SVG(chars+'pinky.svg', False).renderElement('layer1', ghostSize),
        clyde = avg.SVG(chars+'clyde.svg', False).renderElement('layer1', ghostSize),
        green = avg.SVG(chars+'green.svg', False).renderElement('layer1', ghostSize),
        blue2 = avg.SVG(chars+'blue2.svg', False).renderElement('layer1', ghostSize))
    
    boni = '../data/img/bonus/'
    
    arrowSize = (displayWidth/10,displayHeight/12) 
    Bonus.hightLightpic = Ghost.hightLightpic = Ball.hightLightpic = avg.SVG(chars+'arrow.svg', False).renderElement('layer1', arrowSize)
        
    w = (int)(displayWidth/15)
    bonusSize = w,w
    Bonus.pics = dict(
                invertPac=avg.SVG(boni+'invertPac.svg', False).renderElement('layer1', bonusSize),
                newBlock=avg.SVG(boni+'newBlock.svg', False).renderElement('layer1', bonusSize),
                addClyde=avg.SVG(boni+'addClyde.svg', False).renderElement('layer1', bonusSize),
                Bonus4=avg.SVG(boni+'Bonus4.svg', False).renderElement('layer1', bonusSize),
                Bonus5=avg.SVG(boni+'Bonus5.svg', False).renderElement('layer1', bonusSize),
                Bonus6=avg.SVG(boni+'Bonus6.svg', False).renderElement('layer1', bonusSize),
                pacman=avg.SVG(boni+'pacman.svg', False).renderElement('layer1', bonusSize),
                pacShot=avg.SVG(boni+'pacShot.svg', False).renderElement('layer1', bonusSize),
                stopGhosts=avg.SVG(boni+'pacShot.svg', False).renderElement('layer1', bonusSize), # TODO fix pic
                flipGhosts=avg.SVG(boni+'flipGhosts.svg', False).renderElement('layer1', bonusSize),
                wheel=avg.SVG(boni+'wheel.svg', False).renderElement('layer1', bonusSize),
                onlyPong=avg.SVG(boni+'onlyPong.svg', False).renderElement('layer1', bonusSize))