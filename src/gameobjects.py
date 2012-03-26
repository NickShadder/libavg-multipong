'''
Created on 15.02.2012

@author: 2526240
'''

import random
import math
from config import PPM, pointsToWin, ballRadius, ghostRadius, brickSize, maxBatSize, bonusTime, bricksPerLine, brickLines
from libavg import avg, ui
from Box2D import b2EdgeShape, b2PolygonShape, b2FixtureDef, b2CircleShape

cats = {'border':0x0001, 'ghost':0x0002, 'ball':0x0004, 'brick':0x0008, 'redball':0x0010, 'semiborder':0x0020, 'ownball':0x0040}
def dontCollideWith(*categories): return reduce(lambda x, y: x ^ y, [cats[el] for el in categories], 0xFFFF)

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
        self.left = avgNode.pos == (0, 0)
        avgNode.player = self # monkey patch
        left = avgNode.pos == (0, 0)
        angle = math.pi / 2 if left else -math.pi / 2
        pos = (avgNode.width, 2) if left else (0, avgNode.height - 2)            
        # XXX gameobects may obstruct view of the points!
        self.pointsDisplay = avg.WordsNode(parent=avgNode, pivot=(0, 0), pos=pos, angle=angle,
                                           text='Points: 0 / %d' % pointsToWin)
        # TODO does it have to be initialized with so many Nones?! there is no test of the form if raster[x][y] is None!
        self.raster = [[None] * bricksPerLine] * brickLines #Brick-raster
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

    # TODO coordinate with wall
    def addBonus(self, bonus):
        self.boni.append(bonus)
        self.printBoni()

    # TODO coordinate with wall
    def useBonus(self, bonus, node):
        self.boni.remove(bonus)
        node.active = False # XXX animate?
        node.unlink(True)
        bonus.applyEffect(self)
    
    # TODO remove as soon as wall comes 
    def printBoni(self):
        brSPx = brickSize * PPM
        left = self.zone.pos == (0, 0)
        x = 10 if left else self.zone.width - brSPx - 10
        y = len(self.boni) * brSPx + 10
        node = avg.ImageNode(parent=self.zone, pos=(x, y), size=(brSPx, brSPx))
        node.setBitmap(self.boni[-1].pic)
        # normalerweise sollte hier noch Nachruecken sein, aber da diese methode eh weggeht, habe ich keinen bock drauf ;) 
        node.setEventHandler(avg.CURSORDOWN, avg.TOUCH, lambda e, bonus=self.boni[-1], node=node:self.useBonus(bonus, node))

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
            
class GhostBall:
    d = 2 * ballRadius * PPM # TODO make somehow uniform e.g. by prohibiting other ball radii
    pic = avg.SVG('../data/img/char/pacman.svg', False).renderElement('layer1', (d, d))     
    def __init__(self, parentNode, y, left , radius=ballRadius):
        self.diameter = 2 * radius * PPM
        self.width = parentNode.size[0]
        self.node = avg.ImageNode(parent=parentNode, size=(self.diameter, self.diameter))
        self.node.setBitmap(GhostBall.pic)
        # TODO simplify - get rid of left
        if left: 
            self.node.pos = 0, y
            anim = avg.LinearAnim(self.node, 'pos', int(self.width), (int(self.node.pos[0]), int(self.node.pos[1])), (int(self.width), int(self.node.pos[1])), False, None, self.destroy) 
        else:
            self.node.pos = self.width, y
            self.node.angle = math.pi
            anim = avg.LinearAnim(self.node, 'pos', int(self.width), (int(self.width), int(self.node.pos[1])), (-self.diameter, int(self.node.pos[1])), False, None, self.destroy)    
        anim.start()
        
    def destroy(self):
        if self.node is not None:
            self.node.active = False
            self.node.unlink(True)
            self.node = None   

class Ball(GameObject):
    diameter = 2 * ballRadius * PPM
    pic = avg.SVG('../data/img/char/pacman.svg', False).renderElement('layer1', (diameter, diameter))
    def __init__(self, game, renderer, world, parentNode, position):
        GameObject.__init__(self, renderer, world)
        self.game = game
        self.spawnPoint = parentNode.pivot / PPM # XXX maybe make a static class variable
        self.leftPlayer = game.leftPlayer
        self.rightPlayer = game.rightPlayer
        self.lastPlayer = None
        self.node = avg.ImageNode(parent=parentNode)
        self.node.setBitmap(Ball.pic)
        #self.setShadow('FFFF00')
        self.body = world.CreateDynamicBody(position=position, userData=self, active=False, bullet=True) # XXX reevaluate bullet-ness
        self.body.CreateCircleFixture(radius=ballRadius, density=1, restitution=.3,
                                      friction=.01, groupIndex=1, categoryBits=cats['ball'],
                                      maskBits=dontCollideWith('ghost'), userData='ball')

        self.body.CreateCircleFixture(radius=ballRadius, userData='ball', isSensor=True)
        self.nextDir = (random.choice([standardXInertia, -standardXInertia]), random.randint(-10, 10))

        self.__appear(lambda:self.nudge())
        #self.node.setEventHandler(avg.CURSORDOWN, avg.TOUCH, lambda e:self.reSpawn()) # XXX remove
        # self.done = 0
        # g_player.setTimeout(10,self.startPositionCheck)
        
        
#    def startPositionCheck(self):
#        if self.zoneOfPlayer() == self.leftPlayer and not self.done:
#            self.done = 1
#            self.body.linearVelocity = (self.body.linearVelocity[0]/2,self.body.linearVelocity[1]/2)
#        elif self.zoneOfPlayer() == self.rightPlayer and not self.done:
#            self.body.linearVelocity = (self.body.linearVelocity[0]/2,self.body.linearVelocity[1]/2)
#            self.done = 1
#        elif self.zoneOfPlayer() == None:
#            self.done = 0
#        g_player.setTimeout(10,self.startPositionCheck)    

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
#
#class OwnBall(GameObject):
#    leftPic = avg.SVG('../data/img/char/bluepacman.svg', False).renderElement('layer1', (Ball.diameter, Ball.diameter))
#    rightPic = avg.SVG('../data/img/char/greenpacman.svg', False).renderElement('layer1', (Ball.diameter, Ball.diameter))
#    def __init__(self, game, parentNode, owner):
#        
#        self.owner = owner
#        self.node.setBitmap(OwnBall.leftPic if owner.isLeft() else OwnBall.rightPic)        
#        self.body.userData = self
#        for fix in self.body.fixtures:
#            fix.userData = 'ownball'
#            #fix.groupIndex = -2 # XXX test
#            fix.categoryBits = cats['ownball']
#            
#    def getOwner(self):
#        return self.owner

class OwnBall(GameObject):
    d = 2 * ghostRadius * PPM # TODO make somehow uniform e.g. by prohibiting other ghost radii 
    def __init__(self, renderer, world, parentNode, position, owner, left,radius=ghostRadius):
        GameObject.__init__(self, renderer, world)
        self.parentNode = parentNode
        self.trend = 'None'
        self.owner = owner
        self.diameter = 2 * radius * PPM
        self.left = left
        if left:
            self.colored = avg.SVG('../data/img/char/bluepacman.svg', False).renderElement('layer1', (self.diameter, self.diameter))
        else:
            self.colored = avg.SVG('../data/img/char/greenpacman.svg', False).renderElement('layer1', (self.diameter, self.diameter))
        self.node = avg.ImageNode(parent=parentNode, opacity=.85)
        self.node.setBitmap(self.colored)
        self.setShadow('ADD8E6')
        ghostUpper = b2FixtureDef(userData='ownball', shape=b2CircleShape(radius=radius),
                                  density=1, groupIndex= -2, categoryBits=cats['ownball'], maskBits=dontCollideWith('ghost'))
        ghostLower = b2FixtureDef(userData='ownball', shape=b2PolygonShape(box=(radius, radius / 2, (0, -radius / 2), 0)),
                                  density=1, groupIndex= -2, categoryBits=cats['ownball'], maskBits=dontCollideWith('ghost'))
        self.body = world.CreateDynamicBody(position=position, fixtures=[ghostUpper, ghostLower],
                                            userData=self, fixedRotation=True)
        
    def getOwner(self):
        return self.owner

    def render(self):
        pos = self.body.position * PPM - self.node.size / 2
        self.node.pos = (pos[0], pos[1])
        self.node.angle = self.body.angle    
         
        
class RedBall(Ball):
    pic = avg.SVG('../data/img/char/redpacman.svg', False).renderElement('layer1', (Ball.diameter, Ball.diameter))
    def __init__(self, game, parentNode, position,left):
        Ball.__init__(self, game, game.renderer, game.world, parentNode, position)
        self.node.setBitmap(RedBall.pic)
        self.left = left
        self.parentNode = parentNode
        self.body.userData = self
        for fix in self.body.fixtures:
            fix.userData = 'redball'
            #fix.groupIndex = -3 # XXX test
            fix.categoryBits = cats['redball']
            fix.maskBits=dontCollideWith('ball','redball')
    
    # Override
    def nudge(self, direction=None):
        self.body.active = True
        self.body.angularVelocity = 0
        self.body.angle = 0
        if self.left:
            self.body.linearVelocity = (self.parentNode.size[0] / 30, 0) # XXX maybe other than 30
        else:
            self.body.linearVelocity = (-self.parentNode.size[0] / 30, 0) # XXX maybe other than 30
              

class Cloud:    
    pic = avg.SVG('../data/img/char/cloud.svg', False).renderElement('layer1', (500, 1000)) # XXX remove hardcode
    def __init__(self, parentNode):
        self.parentNode = parentNode
        self.node = avg.ImageNode(parent=parentNode, opacity=1, pos=(0, 0))
        self.node.setBitmap(Cloud.pic)
        # TODO this can't be it
                
class SemipermeableShield(GameObject):
    def __init__(self, game, left, *noCollisions):
        self.world = game.world
        self.game = game
        self.parentNode = game.display
        self.left = left
        
        # TODO no need for two different images - just rotate ;)
        if left:
            self.pic = avg.SVG('../data/img/char/semiperleft.svg', False).renderElement('layer1', (PPM * 2, self.parentNode.size[1]))
            self.x = self.parentNode.size[0] / 3
            self.w = 2
        else:
            self.pic = avg.SVG('../data/img/char/semiperright.svg', False).renderElement('layer1', (PPM * 2, self.parentNode.size[1]))
            self.x = 2 * self.parentNode.size[0] / 3 - (PPM * 2)
            self.w = 0        
        
        self.node = avg.ImageNode(parent=self.parentNode, opacity=1, pos=(self.x, 0))
        self.node.setBitmap(self.pic)
        
        self.body = self.world.CreateStaticBody(position=(0, 0), userData=self)
        self.body.CreateFixture(shape=b2EdgeShape(vertices=[(self.x / PPM + self.w, 0), (self.x / PPM + self.w, self.parentNode.size[1] / PPM)]), density=1,
                                restitution=1, categoryBits=cats['semiborder'], userData='semiborder', maskBits=dontCollideWith(*noCollisions))
    
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
    diameter = 2 * ghostRadius * PPM 
    blue = avg.SVG('../data/img/char/blue.svg', False).renderElement('layer1', (diameter, diameter))
    def __init__(self, renderer, world, parentNode, position, name, owner=None, mortal=1):
        GameObject.__init__(self, renderer, world)
        self.parentNode = parentNode
        self.spawnPoint = position
        self.name = name
        self.trend = None
        self.owner = owner
        self.mortal = mortal
        self.colored = avg.SVG('../data/img/char/' + name + '.svg', False).renderElement('layer1', (Ghost.diameter, Ghost.diameter)) # TODO make this faster (use static dict)
        self.node = avg.ImageNode(parent=parentNode, opacity=.85)
        self.setShadow('ADD8E6')
        ghostUpper = b2FixtureDef(userData='ghost', shape=b2CircleShape(radius=ghostRadius),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'], maskBits=dontCollideWith('ball'))
        ghostLower = b2FixtureDef(userData='ghost', shape=b2PolygonShape(box=(ghostRadius, ghostRadius / 2, (0, -ghostRadius / 2), 0)),
                                  density=1, groupIndex= -1, categoryBits=cats['ghost'], maskBits=dontCollideWith('ball'))
        self.body = world.CreateDynamicBody(position=position, fixtures=[ghostUpper, ghostLower],
                                            userData=self, fixedRotation=True)
        self.changeMortality()
        self.render()
        self.move()
        
#        ui.DragRecognizer(self.node, moveHandler=self.onMove) # XXX just for debugging and fun
#    def onMove(self, event, offset):
#        self.body.position = event.pos / PPM
    
    def getDir(self):
        return self.body.linearVelocity
    
    def getOwner(self):
        return self.owner
             
    def flipState(self):
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
        # TODO fix bug: sometimes body is None
        self.body.position = pos
        self.mortal = 0 # ghost respawns in immortal state XXX rerender this?
        self.render()
        self.node.active = True
        avg.fadeIn(self.node, 1000, .85, lambda:self.body.__setattr__('active', True)) 
        
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
        g_player.clearInterval(self.movement)
        self.body.linearVelocity = (0, 0)
        g_player.setTimeout(2000, self.move)    
        
    def changeMortality(self):
        # TODO implement some kind of AI
        self.changing = g_player.setTimeout(random.choice([2000, 3000, 4000, 5000, 6000]), self.changeMortality) # XXX store ids for stopping when one player wins
        if self.body and self.body.active: # just to be sure ;)
            self.flipState()

            
#class OwnBall(GameObject):
#    d = 2 * ghostRadius * PPM 
#    def __init__(self, renderer, world, parentNode, position, owner, left,radius=ghostRadius):
#        GameObject.__init__(self, renderer, world)
#        self.parentNode = parentNode
#        self.trend = 'None'
#        self.owner = owner
#        self.diameter = 2 * radius * PPM
#        self.left = left
#        if left:
#            self.colored = avg.SVG('../data/img/char/bluepacman.svg', False).renderElement('layer1', (self.diameter, self.diameter))
#        else:
#            self.colored = avg.SVG('../data/img/char/greenpacman.svg', False).renderElement('layer1', (self.diameter, self.diameter))
#        self.node = avg.ImageNode(parent=parentNode, opacity=.85)
#        self.node.setBitmap(self.colored)
#        self.setShadow('ADD8E6')
##        ghostUpper = b2FixtureDef(userData='ownball', shape=b2CircleShape(radius=radius),
##                                  density=1, groupIndex= -2, categoryBits=cats['ownball'], maskBits=dontCollideWith('ghost'))
##        ghostLower = b2FixtureDef(userData='ownball', shape=b2PolygonShape(box=(radius, radius / 2, (0, -radius / 2), 0)),
##                                  density=1, groupIndex= -2, categoryBits=cats['ownball'], maskBits=dontCollideWith('ghost'))
##        self.body = world.CreateDynamicBody(position=position, fixtures=[ghostUpper, ghostLower],
##                                            userData=self, fixedRotation=True)
#        fixtureDef = b2FixtureDef (userData='ownball', shape=b2CircleShape(radius=radius), density=1, groupIndex= -2, categoryBits=cats['ownball'], maskBits=dontCollideWith('ghost'),
#                                  friction=.03, restitution=1)
#        self.body = self.world.CreateStaticBody(position=position, userData=self)
#        self.body.CreateFixture(fixtureDef)
#        
#       
#        self.render()
#        
#    def getOwner(self):
#        return self.owner
#
#    def render(self):
#        pos = self.body.position * PPM - self.node.size / 2
#        self.node.pos = (pos[0], pos[1])
#        self.node.angle = self.body.angle
        
        

    
'''

TOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOODOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO

- Bessere Grafiken
- Weitere Boni implementieren
- Bestehende Boni verbessern
    - Anzahl der Geister abfragen(ein Bonus killt alle, einer fuegt welche hinzu)
        - "Nonefehler" verhindern
    - Zeiten der Boni entscheiden (Dauer des Effekts, Dauer bis zum naechsten Bonus)
- Tetris und Boni verbinden


DERZEITIG SINNVOLLSTE BONUSLISTE

SCHUTZ

-    Geschuetzturm [x]
-     Tetrisblock [x]
-    Kraftfeld [x]

ANGRIFF

-     PACMAN-Dreier-Shot [x]
-    Gegnerischen Schlaeger ausschalten 
-    Startpunkt fuer PAC zufaellig und Richtung immer nur in eine Richtung, Gegner
-     Schwarzer PACMAN, frisst anderen PACMAN, Spieler bekommt Punkt
-     Nebel ueber gegnerischem Feld

    
Allgemein

-    PACMAN invertiert seine flugrichtung [x]
-     Geister stoppen kurz [x]
-    PACMAN wird kleiner [x]                                                         - Achtung! - koennte in der Wand "stecken" bleiben
-    Extra Geist, der nur einen Spieler beeinflusst [x]
-    Geister halten sich nur auf der anderen Seite auf [x]
-    Ball fliegt auf der eigenen Haelfte langsamer
-    1 Punkt                                
-    Shuffle
-    Pongmode
-    Pacmanmode

Eher nicht:

-    PAC frisst auch farbige Geister
-     Schwarzes Loch saugt Geister auf, lenk Ball ab
-    PAC stirbt durch blaue Geister
-     PAC bekommt die Farbe eines Geists
-    1/2 Gesammelte Punkte
-     Alle Geister verschwinden, fuer ein paar Sekunden
-     Alle Geister werden wieder unsterblich oder umgekehrt
-    Die Wand verdoppelt sich
-     Asteroidenhagel
-    Siegeskarte 
-    Die Haelfte der Wand verschwindet

ETSILSUNOB ETSLLOVNNIS GITIEZRED

OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOODOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOT

'''    
                                
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
    def __init__(self, world, game, parentNode, position, number, left=False):
        self.size = (150, 150) # XXX I don't like explicit numbers like these
        self.pos = (0, 0)
        self.pic = avg.SVG('../data/img/char/Wheel.svg', False).renderElement('layer1', self.size) # TODO make faster
        self.parentNode, self.game, self.world = parentNode, game, world
        self.left = left
        if left:
            self.node = avg.ImageNode(parent=parentNode, pos=(position[0] - self.size[0], position[1] - self.size[1]), angle=0)
            self.pos = (position[0] - self.size[0], position[1] - self.size[1])
        else:
            self.node = avg.ImageNode(parent=parentNode, pos=(position[0], position[1] - self.size[1]), angle=0)
            self.pos = (position[0], position[1] - self.size[1])
            
        self.node.setBitmap(self.pic)
        self.anim = avg.LinearAnim(self.node, 'angle', 2000, 0, 3.14, False, None, self.restartanim).start()
        g_player.setTimeout(1000 + (number * 1000), self.fire)
        g_player.setTimeout(30000 + (number * 1000), self.destroy)
        
    def restartanim(self):
        if self.node is not None:
            self.anim = avg.LinearAnim(self.node, 'angle', 2000, 0, 3.14, False, None, self.restartanim).start()
    
    def fire(self):
        if self.node is not None:
            self.game.getRedBalls().append(RedBall(self.game,self.parentNode, 
                    (self.pos[0] / PPM + (self.size[0]) / (2 * PPM), self.pos[1] / PPM + (self.size[1] / (2 * PPM))),
                    self.left))
            g_player.setTimeout(3000, self.fire)
        
    def destroy(self):
        if self.anim is not None:
            self.anim.abort()
            self.anim = None
        if self.node is not None:
            self.node.active = False
            self.node.unlink(True)
            self.node = None

class Bonus:
    bonusSize = (50,50)
    pics = dict(
                invertPac=avg.SVG('../data/img/char/invertPac.svg', False).renderElement('layer1', bonusSize),
                newBlock=avg.SVG('../data/img/char/newBlock.svg', False).renderElement('layer1', bonusSize),
                addClyde=avg.SVG('../data/img/char/addClyde.svg', False).renderElement('layer1', bonusSize),
                Bonus4=avg.SVG('../data/img/char/Bonus4.svg', False).renderElement('layer1', bonusSize),
                Bonus5=avg.SVG('../data/img/char/Bonus5.svg', False).renderElement('layer1', bonusSize),
                Bonus6=avg.SVG('../data/img/char/Bonus6.svg', False).renderElement('layer1', bonusSize),
                pacman=avg.SVG('../data/img/char/pacman.svg', False).renderElement('layer1', bonusSize),
                pacShot=avg.SVG('../data/img/char/pacShot.svg', False).renderElement('layer1', bonusSize),
                stopGhosts=avg.SVG('../data/img/char/stopGhosts.svg', False).renderElement('layer1', bonusSize),
                flipGhosts=avg.SVG('../data/img/char/flipGhosts.svg', False).renderElement('layer1', bonusSize),
                wheel=avg.SVG('../data/img/char/wheel.svg', False).renderElement('layer1', bonusSize),
                onlyPong=avg.SVG('../data/img/char/onlyPong.svg', False).renderElement('layer1', bonusSize)
                )
    def __init__(self, game, (name, effect)):
        parentNode = game.display
        displayWidth = parentNode.size[0]
        displayHeight = parentNode.size[1] 
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
        
    def onClick(self, event):
        g_player.clearInterval(self.timeout)
        res = event.node == self.leftBonus
        self.vanish()
        return res

    def vanish(self):
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
        
    def pacShot(self, player):
        height = self.parentNode.size[1]
        GhostBall(self.parentNode, (1 * height) / 4, player.isLeft())
        GhostBall(self.parentNode, (2 * height) / 4, player.isLeft())
        GhostBall(self.parentNode, (3 * height) / 4, player.isLeft())
        
    def flipGhostStates(self, player=None):    
        if self.game.getGhosts():
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
        if len(self.game.getGhosts()) > 0:
            self.game.killGhosts()
        
    def bringBackGhosts(self, player=None):
        if len(self.game.getGhosts()) == 0:
            self.game.createGhosts()
         
    def addGhost(self, player):
        if player.isLeft():
            self.game.ghosts.append(Ghost(self.game.renderer, self.world, self.parentNode, self.game.middle - (0, (ballRadius + ghostRadius) * 2), "blue2", player))
        else:
            self.game.ghosts.append(Ghost(self.game.renderer, self.world, self.parentNode, self.game.middle - (0, (ballRadius + ghostRadius) * 2), "green", player))
        
    def setGhostToOpponent(self, player):
        for g in self.game.getGhosts():
            if player.isLeft():
                g.setTrend('right')
            else:
                g.setTrend('left')
                                  
    def setTowers(self, player):
        x = self.parentNode.size[0]
        y = self.parentNode.size[1]
        n = 4
        if self.game.leftPlayer == player:
            for i in range(1, n):  
                Tower(self.world, self.game,self.parentNode,(x/3,i*y/3),i,1)
        else:
            for i in range(1, n):  
                Tower(self.world, self.game,self.parentNode,(2*x/3,i*y/3),i, 0)
            
    def newOwnBall(self, player=None):
        if player.isLeft():
            OwnBall(self.game.renderer, self.world, self.parentNode, (random.randint(0,self.parentNode.size[0]/PPM),random.randint(0,self.parentNode.size[1]/PPM)),player,1)
        else:
            OwnBall(self.game.renderer, self.world, self.parentNode, (random.randint(0,self.parentNode.size[0]/PPM),random.randint(0,self.parentNode.size[1]/PPM)),player,0)
          
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
    boni = dict(pacShot=Bonus.pacShot,
                stopGhosts=Bonus.stopGhosts,
                flipGhosts=Bonus.flipGhostStates,
                wheel=Bonus.setTowers,
                onlyPong=Bonus.buildShield,
                pacman=Bonus.newOwnBall)




      
        
    def __init__(self, game, (name, effect)):
        Bonus.__init__(self, game, (name, effect))
    
    def onClick(self, event):
        (self.game.leftPlayer if Bonus.onClick(self, event) else self.game.rightPlayer).addBonus(self)  
        
class InstantBonus(Bonus):
    
#    boni = dict(invertPac=Bonus.invertPac,
#                newBlock=Bonus.newBlock,
#                addClyde=Bonus.addGhost,
#                Bonus4=Bonus.hideGhosts,
#                Bonus5=Bonus.bringBackGhosts,
#                Bonus6=Bonus.setGhostToOpponent,
#                pacman=Bonus.newOwnBall)
    
    boni = dict( pacman=Bonus.newOwnBall)

          
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
            
class Bat(GameObject): # XXX MAYBE GHOST ARE NOT AFFECTED BY BAT 
    batImgLen = max(1, maxBatSize * PPM / 2)
    batImgWidth = max(1, batImgLen / 10)
    blueBat = avg.SVG('../data/img/char/bat_blue.svg', False).renderElement('layer1', (batImgWidth, batImgLen))
    greenBat = avg.SVG('../data/img/char/bat_green.svg', False).renderElement('layer1', (batImgWidth, batImgLen))
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
        self.parentNode = parentNode
        if self.material is None:
            self.material = random.choice(filter(lambda x:type(x).__name__ == 'tuple', Material.__dict__.values())) # XXX hacky
        self.node = avg.ImageNode(parent=parentBlock.container, pos=pos)
        self.node.setBitmap(self.material[1][0])
        self.__index = None

    # spawn a physical object
    def materialize(self, onLeft, x, y, pos=None):
        if pos is None:
            pos = (self.node.pos + self.node.pivot) / PPM # TODO this looks like trouble
        self.node.unlink()
        self.parentNode.appendChild(self.node)
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
            if self.block.onLeft:
                player = self.block.leftPlayer
            else:
                player = self.block.rightPlayer
            player.raster[self.__index[0]][self.__index[1]] = None
            self.destroy() # XXX maybe override destroy for special effects, or call something like vanish first

    def render(self):
        pass # XXX move the empty method to GameObject when the game is ready

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
        self.__timeCall = None
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
            widthDisplay = self.parentNode.size[1]
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
        cellList = []
        possible = True
        for b in self.brickList:
            (x, y) = self.__calculateIndices(b.node.pos)
            if (x >= brickLines):
                possible = False
            else:
                if self.onLeft:
                    cellList.append(self.leftPlayer.raster[x][y])
                else:
                    cellList.append(self.rightPlayer.raster[x][y])
        if possible:
            for co in cellList:
                if co != None:
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
        if y >= bricksPerLine:
            y = bricksPerLine - 1
        elif y < 0:
            y = 0
        if x < 0:
            x = 0
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
        self.__displayRaster(False)
        if self.__timeCall is not None:
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
            self.__displayRaster(False)
    
    def __displayRaster(self, on):
        if self.onLeft:
            raster = self.leftPlayer.nodeRaster
        else:
            raster = self.rightPlayer.nodeRaster
        for n in raster:
                n.active = on
