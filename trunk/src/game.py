'''
Created on 19.01.2012

@author: 2526240
'''
import sys
import random

from libavg import avg, gameapp, statemachine, ui
from Box2D import b2World, b2Vec2, b2ContactListener
import math

import gameobjects
from gameobjects import Ball, Bat, Ghost, Player, BorderLine, PersistentBonus, InstantBonus, Block, Mine, RedBall, Tower, Bonus,timeForStep
from config import PPM, TIME_STEP, maxBalls, ballRadius, maxBatSize, ghostRadius, brickSize, brickLines

g_player = avg.Player.get()
def a2w(coords):
    return b2Vec2(coords[0], coords[1]) / PPM

class Renderer:
    def __init__(self):
        self.objects = set()
    def register(self, *pyboxObjects):
        self.objects.update(pyboxObjects)
    
    def deregister(self, *pyboxObjects):
        self.objects.difference_update(pyboxObjects)
    def draw(self):
        for obj in self.objects:
            obj.render()

class ContactListener(b2ContactListener):   
    def __init__(self, hitset):
        b2ContactListener.__init__(self)
        self.hitset = hitset
    def EndContact(self, contact):
        fA, fB = contact.fixtureA, contact.fixtureB
        dA, dB = fA.userData, fB.userData
        ball = red = brick = bat = semi = None
        found = False
        if dA == 'ball': 
            ball = fA.body.userData
            found = True
        elif dA == 'bat':
            bat = fA.body.userData
            found = True
        elif dA == 'redball':
            red = fA.body.userData
            found = True
        elif dA == 'brick':
            brick = fA.body.userData
            found = True
        elif dA == 'semiborder':
            semi = fA.body.userData
            found = True
        if not found: return
        
        found = False
        if dB == 'ball': 
            ball = fB.body.userData
            found = True
        elif dB == 'bat':
            bat = fB.body.userData
            found = True
        elif dB == 'redball':
            red = fB.body.userData
            found = True
        elif dB == 'brick':
            brick = fB.body.userData
            found = True
        elif dB == 'semiborder':
            semi = fB.body.userData
            found = True
        if not found: return
        
        if brick is not None:
            if ball is not None:
                self.hitset.add(brick)
            elif red is not None:
                self.hitset.add(brick)
                self.hitset.add(red)
        elif semi is not None:
            if red is not None:
                if semi.ownedByLeft() != red.left:
                    self.hitset.add(red)
        elif bat is not None:
            if red is not None:
                self.hitset.add(red)
                
    def PreSolve(self, contact, oldManifold):
        fA, fB = contact.fixtureA, contact.fixtureB
        dA, dB = fA.userData, fB.userData
        ball = bat = semi = red= None
        found = False
        if dA == 'ball': 
            ball = fA.body.userData
            found = True
        elif dA == 'bat':
            bat = fA.body.userData
            found = True
        elif dA == 'semiborder':
            semi = fA.body.userData
            found = True
        elif dA == 'redball':
            red = fA.body.userData
            found = True
        if not found: return
        
        found = False
        if dB == 'ball':
            ball = fB.body.userData
            found = True
        if dB == 'bat':
            bat = fB.body.userData
            found = True
        if dB == 'semiborder':
            semi = fB.body.userData
            found = True
        elif dB == 'redball':
            red = fB.body.userData
            found = True
        if not found: return       
            
        if bat is not None and ball is not None:
            ball.lastPlayer = bat.zone.player
            
        elif semi is not None:
            if ball is not None or red is not None:
                worldManifold = contact.worldManifold
                if semi.ownedByLeft():
                    if worldManifold.normal.x < 0:
                        contact.enabled=False
                elif worldManifold.normal.x > 0:
                    contact.enabled=False
                    
class Game(gameapp.GameApp):
    def init(self):
        gameobjects.displayWidth,gameobjects.displayHeight = self._parentNode.size
        gameobjects.bricksPerLine = (int)(self._parentNode.size[1]/(brickSize*PPM))
        gameobjects.preRender()
        self.tutorialMode = False
        self.machine = statemachine.StateMachine('BEMOCK', 'MainMenu')
        self.machine.addState('MainMenu', ['Playing', 'Tutorial', 'About'], enterFunc=self.showMenu, leaveFunc=self.hideMenu)
        self.machine.addState('Tutorial', ['MainMenu', 'Playing', 'Tutorial'], enterFunc=self.startTutorial, leaveFunc=self.hideTutorial)
        self.machine.addState('Playing', ['Winner'], enterFunc=self.startPlaying)
        self.machine.addState('Winner', ['Playing', 'MainMenu']) # XXX clarify this stuff
        self.machine.addState('About', ['MainMenu'], enterFunc=self.showAbout, leaveFunc=self.hideAbout)
    
        self.createMenuBackground()
        self.showMenu()

    def _makeButtonInMiddle(self, name, node, yOffset, pyFunc):
        path = '../data/img/btn/'
        svg = avg.SVG(path + name + '_up.svg', False)
        height = node.height / 8 # XXX make dependant on actual resolution sometime
        size = (height * 2.4, height)
        upNode = svg.createImageNode('layer1', {}, size)
        svg = avg.SVG(path + name + '_dn.svg', False)
        downNode = svg.createImageNode('layer1', {}, size)
        position = (node.pivot[0] - upNode.width / 2, node.pivot[1] + yOffset * upNode.height + yOffset * 50)
        return ui.TouchButton(upNode, downNode, clickHandler=pyFunc, parent=node, pos=position)

    def showMenu(self):
        self.menuScreen = avg.DivNode(parent=self._parentNode, size=self._parentNode.size)
        self.startButton = self._makeButtonInMiddle('start', self.menuScreen, -1, lambda:self.machine.changeState('Playing'))
        self.tutorialButton = self._makeButtonInMiddle('help', self.menuScreen, 0, lambda:self.machine.changeState('Tutorial'))
        self.aboutButton = self._makeButtonInMiddle('about', self.menuScreen, 1, lambda:self.machine.changeState('About'))
        self.exitButton = self._makeButtonInMiddle('exit', self.menuScreen, 2, lambda:exit(0))

        
    def createMenuBackground(self):   
        self.nodeList = []
        picList = [Ball.pic,Mine.leftPic,Mine.rightPic,RedBall.pic,Tower.pic,Bat.blueBat,Bat.greenBat,Bonus.highLightpic] + Ghost.pics.values() + Bonus.pics.values() # TODO WHY RED

        for i in range (1,random.randint(100,200)):
            node = avg.ImageNode(parent=self._parentNode, opacity=1)
            node.setBitmap(random.choice(picList))
            node.pos = (random.randint(0,int(self._parentNode.size[0]/3)) if random.randint(0,1) else random.randint(2*int(self._parentNode.size[0]/3),int(self._parentNode.size[0])),random.randint(0,int(self._parentNode.size[1])))
            self.nodeList.append(node)
        self.title = avg.WordsNode(
                                    parent=self._parentNode, 
                                    pivot=(0, 0),
                                    text="Multipong", 
                                    pos= (self._parentNode.size[0]/2- 100,50),
                                    wrapmode="wordchar", 
                                    font= 'Impact', 
                                    color = "00FF00",
                                    fontsize=100,
                                    variant="bold")
            
    def destroyMenuBackground(self):
        for node in self.nodeList:
            node.active = False
            node.unlink(True)
            node = None 
        
        self.title.active = False
        self.title.unlink(True)
        self.title = None
                     
    def hideMenu(self):
        # XXX find out if we need to tear down all the buttons first
        self.menuScreen.unlink(True)
        self.menuScreen = None
        
    def startTutorial(self):
        self.tutorialMode = True
        self.startPlaying()
    
    def hideTutorial(self):
        # TODO implement this by simply tearing down what you have built in startTutorial ;)
        pass

    def showAbout(self):
        self.aboutScreen = avg.DivNode(parent=self._parentNode, size=self._parentNode.size)
        avg.WordsNode(parent=self.aboutScreen, x=5, text='Unnamed Multipong<br/>as envisioned and implemented by<br/>Benjamin Guttman<br/>Joachim Couturier<br/>Philipp Hermann<br/>Mykola Havrikov<br/><br/>This game uses libavg(www.libavg.de) and PyBox2D(http://code.google.com/p/pybox2d/)')
        self.menuButton = self._makeButtonInMiddle('menu', self.aboutScreen, 1, lambda:self.machine.changeState('MainMenu'))

    def hideAbout(self):
        self.aboutScreen.unlink(True)
        self.aboutScreen = None
        

    def startPlaying(self):
        # libavg setup
        self.destroyMenuBackground()
        self.display = avg.DivNode(parent=self._parentNode, size=self._parentNode.size)
        self.renderer = Renderer()
#        background = avg.ImageNode(parent = self.display)
#        background.setBitmap(avg.SVG('../data/img/char/background.svg', False).renderElement('layer1', self.display.size))
        self.display.player = None # monkey patch
        (displayWidth, displayHeight) = self.display.size
        widthThird = (int)(displayWidth / 3)
        fieldSize = (widthThird, displayHeight)
        self.field1 = avg.DivNode(parent=self.display, size=fieldSize)
        self.field2 = avg.DivNode(parent=self.display, size=fieldSize, pos=(displayWidth - widthThird, 0))
        avg.LineNode(parent=self.display, pos1=(0, 1), pos2=(displayWidth, 1))
        avg.LineNode(parent=self.display, pos1=(0, displayHeight), pos2=(displayWidth, displayHeight))
        svg = avg.SVG('../data/img/btn/dotted_line.svg', False)
        svg.createImageNode('layer1', dict(parent=self.display, pos=(widthThird, 0)), (2, displayHeight))
        svg.createImageNode('layer1', dict(parent=self.display, pos=(displayWidth - widthThird, 0)), (2, displayHeight))
        
        # pybox2d setup
        self.world = b2World(gravity=(0, 0), doSleep=True)
        self.hitset = set()
        self.listener = ContactListener(self.hitset)
        self.world.contactListener = self.listener
        
        self.leftPlayer, self.rightPlayer = Player(self, self.field1), Player(self, self.field2)
        self.leftPlayer.other, self.rightPlayer.other = self.rightPlayer, self.leftPlayer # monkey patch ftw =)
        
        # horizontal lines
        BorderLine(self.world, a2w((0, 1)), a2w((displayWidth, 1)), 1, False, 'redball')
        BorderLine(self.world, a2w((0, displayHeight)), a2w((displayWidth, displayHeight)), 1, False, 'redball')
        # vertical ghost lines
        maxWallHeight = (brickSize*brickLines+ghostRadius)*PPM
        BorderLine(self.world, a2w((maxWallHeight, 0)), a2w((maxWallHeight, displayHeight)), 1, False, 'redball', 'ball') 
        BorderLine(self.world, a2w((displayWidth-maxWallHeight-1, 0)), a2w((displayWidth-maxWallHeight-1, displayHeight)), 1, False, 'redball', 'ball')
        self.middleX,self.middleY = self.display.size / 2
        self.middle = a2w((self.middleX, self.middleY))
        BatManager(self.field1, self.world, self.renderer)
        BatManager(self.field2, self.world, self.renderer)
        self.balls = []
        self.redballs = []
        self.ghosts = []
        self.createBall()
        self.initiateBlocks()
        self.mainLoop = g_player.setInterval(13, self.step)
                
    def initiateBlocks(self):
        height = (self.display.size[1] / 2) - (brickSize * PPM)
        width = self.display.size[0]
        for i in range (-3,3):
            Block(self.display, self.renderer, self.world, (width / 3 - (brickSize * 5 * PPM), height - (brickSize*PPM*3)*i ), (self.leftPlayer, self.rightPlayer), random.choice(Block.form.values()))
            Block(self.display, self.renderer, self.world, (2 * width / 3, height - (brickSize*PPM*3)*i ), (self.leftPlayer, self.rightPlayer), random.choice(Block.form.values()))
            timeForStep(self.display,1)
            timeForStep(self.display,0)
        
    def createBall(self):
        ball = Ball(self, self.renderer, self.world, self.display, self.middle)
        self.balls.append(ball)

        if self.tutorialMode:
            ball.highLight()
            g_player.setTimeout(25000, self.createGhosts)
        else:
            self.createGhosts()
            
    def createGhosts(self):
        offset = 2*ballRadius + 3*ghostRadius
        self.ghosts.append(Ghost(self.renderer, self.world, self.display, self.middle + (offset,offset), "blinky"))
        self.ghosts.append(Ghost(self.renderer, self.world, self.display, self.middle + (-offset,offset), "pinky"))
        self.ghosts.append(Ghost(self.renderer, self.world, self.display, self.middle - (-offset,offset), "inky"))
        self.ghosts.append(Ghost(self.renderer, self.world, self.display, self.middle - (offset,offset), "clyde"))   
        if self.tutorialMode:
            g_player.setTimeout(25000, self._bonusJobForTutorial)
            for ghost in self.ghosts:
                ghost.highLight(self.field1,self.field2)         
        else:
            g_player.setTimeout(3000, self._bonusJob)       
             
    def killGhosts(self):
        for ghost in self.ghosts:        
            ghost.destroy()
        del self.ghosts[:]
                        
    def getBalls(self):
        return self.balls
    
    def getRedBalls(self):
        return self.redballs
    
    def getGhosts(self):
        return self.ghosts
    
    def _bonusJobForTutorial(self):        
        if len(InstantBonus.boni.items()) > 0:
            bonus = InstantBonus(self, InstantBonus.boni.popitem())
            bonus.highLight(self.field1,self.field2)
        elif len(PersistentBonus.boni.items()) > 0:
            bonus = PersistentBonus(self, PersistentBonus.boni.popitem())
            bonus.highLight(self.field1,self.field2)
        else:
            pass     
        g_player.setTimeout(5000, self._bonusJobForTutorial)
        
    def _bonusJob(self):
        nextBonus = random.randint(0,2)
        if nextBonus == 0:
            PersistentBonus(self, random.choice(PersistentBonus.boni.items()))
        elif nextBonus == 1:
            InstantBonus(self, random.choice(InstantBonus.boni.items()))
        else:
            InstantBonus(self, ('newBlock',InstantBonus.boni['newBlock']))
        self.bonusjob = g_player.setTimeout(random.choice([4000, 5000, 6000]), self._bonusJob)

    def win(self, player):
        g_player.clearInterval(self.mainLoop)
        if self.bonusjob is not None:
            g_player.clearInterval(self.bonusjob)            
        for ghost in self.ghosts:
            if ghost.movement is not None:
                g_player.clearInterval(ghost.movement)
            if ghost.changing is not None:
                g_player.clearInterval(ghost.changing)
        # abort all anims and intervals
        # TODO tear down world and current display
        # TODO show winner/revanche screen
      
    def addBall(self):
        if len(self.balls) < maxBalls:
            self.balls.append(Ball(self, self.renderer, self.world, self.display, self.middle))
    
    def removeBall(self, ball):
        if len(self.balls)>1:
            self.balls.remove(ball)
            ball.destroy()

    def _processBallvsBrick(self, hitset):
        copy = hitset.copy()
        for brick in copy:
            brick.hit()
        hitset.difference_update(copy)
        copy.clear() # just cause I feel like cleaning up
        
    def _processBallvsBall(self):
        for ball in self.balls:
            for ce in ball.body.contacts:
                contact = ce.contact
                mine  = None
                if contact.fixtureA.userData == 'mine':
                    mine = contact.fixtureA.body.userData                
                elif contact.fixtureB.userData == 'mine':
                    mine = contact.fixtureB.body.userData
                    
                if mine is not None:
                    if ball.lastPlayer != mine.getOwner() and ball.lastPlayer is not None:
                        ball.lastPlayer.removePoint()
                        ball.reSpawn()
                        mine.destroy()
                        return

    def _processBallvsGhost(self):
        for ball in self.balls:
            for ce in ball.body.contacts:
                contact = ce.contact
                ghost = None        
                if contact.fixtureA.userData == 'ghost':
                    ghost = contact.fixtureA.body.userData
                
                elif contact.fixtureB.userData == 'ghost':
                    ghost = contact.fixtureB.body.userData
                            
                if ghost is not None:
                    if ghost.mortal:
                        # ball eats ghost
                        ghost.reSpawn()
                        if ball.lastPlayer is not None:
                            ball.lastPlayer.addPoint()
                        self.addBall()
                        break
                    else:
                        # ghost eats ball
                        player = ball.zoneOfPlayer()
                        if player is not None and ghost.getOwner() != player:
                            player.removePoint()   
                        if len(self.balls) <= 1:    # XXX maybe introduce minBalls
                            ball.reSpawn()
                        else:
                            self.removeBall(ball)
                        break

    def _checkBallPosition(self):
        for ball in self.balls:
            if ball.body.position[0] > (self.display.size[0] / PPM) + ballRadius: 
                self.leftPlayer.addPoint()
                ball.reSpawn()
            elif ball.body.position[0] < -ballRadius: 
                self.rightPlayer.addPoint()
                ball.reSpawn()
    
    def _outside(self,ball):
        return (ball.body is None or 
                not (-ballRadius <= ball.body.position[0] <= (self.display.size[0] / PPM) + ballRadius))
    
    def _checkRedBallPosition(self):
        killList = [x for x in self.redballs if self._outside(x)]
        self.redballs[:] = [x for x in self.redballs if x not in killList]
        for ball in killList:
            ball.destroy()
                                                   
    def step(self):
        self.world.Step(TIME_STEP, 10, 10)
        self.world.ClearForces()
        self._processBallvsGhost()
        self._checkBallPosition()
        self._checkRedBallPosition()
        self._processBallvsBall()
        self._processBallvsBrick(self.hitset)
        self.renderer.draw()             

class BatManager:
    # XXX remove all the assertions some time
    def __init__(self, parentNode, world, renderer):
        self.world, self.field, self.renderer = world, parentNode, renderer
        self.machine = statemachine.StateMachine('manager', 'idle')
        self.machine.addState('idle', ['started'])
        self.machine.addState('started', {'idle':self.reset, 'created':None})
        self.machine.addState('created', ['started'], enterFunc=self.createBat, leaveFunc=self.destroyBat)
        self.pos = [] # it's a list of tuples of the form (cursorid, position)  
        self.bat = None
        self.field.setEventHandler(avg.CURSORDOWN, avg.TOUCH, self.onDown)
        #self.field.setEventHandler(avg.CURSORUP, avg.TOUCH, self.onUp)
        self.field.setEventHandler(avg.CURSOROUT, avg.TOUCH, self.onUp)
        self.rec = ui.TransformRecognizer(self.field, moveHandler=self.onTransform)
        
    def reset(self):
        assert len(self.pos) > 0
        del self.pos[:]
        assert len(self.pos) == 0
        self.destroyBat()
    
    def destroyBat(self):
        if self.bat is not None:
            self.bat.destroy()
            self.bat = None
    
    def createBat(self):
        self.bat = Bat(self.renderer, self.world, self.field, [p[1] for p in self.pos])

    def onDown(self, e):
        state = self.machine.state
        if state == 'idle':
            assert len(self.pos) == 0
            self.pos.append((e.cursorid, e.pos))
            self.field.setEventCapture(e.cursorid)
            assert len(self.pos) == 1
            self.machine.changeState('started')
        elif state == 'started':
            assert len(self.pos) == 1
            if (e.pos - self.pos[0][1]).getNorm() <= maxBatSize * PPM:
                self.pos.append((e.cursorid, e.pos))
                self.field.setEventCapture(e.cursorid)
                assert len(self.pos) == 2
                self.machine.changeState('created')

    def onUp(self, e):
        state = self.machine.state
        cid = e.cursorid
        if state == 'started':
            assert len(self.pos) == 1
            if cid == self.pos[0][0]:
                self.field.releaseEventCapture(cid)
                self.machine.changeState('idle')
        elif state == 'created':
            assert len(self.pos) == 2            
            if cid == self.pos[1][0]:
                self.field.releaseEventCapture(cid)
                del self.pos[1]
                assert len(self.pos) == 1
                self.machine.changeState('started')
            elif cid == self.pos[0][0]:
                self.field.releaseEventCapture(cid)
                del self.pos[0]
                assert len(self.pos) == 1
                self.machine.changeState('started')
                
    def onTransform(self, tr):
        if self.bat is not None:
            # ugly
            vert = [(tr.scale * v[0], tr.scale * v[1]) for v in self.bat.body.fixtures[0].shape.vertices]
            pos1, pos2 = avg.Point2D(vert[0]), avg.Point2D(vert[1])
            length = (pos2 - pos1).getNorm()
            self.bat.body.active = self.bat.node.active = length <= maxBatSize 
            width = max(1 / PPM, (maxBatSize - length) / 10)
            self.bat.body.fixtures[0].shape.SetAsBox(length / 2, width / 2)
            self.bat.body.position = tr.pivot / PPM 
            self.bat.body.position += tr.trans / PPM
            self.bat.body.angle += tr.rot
            
            res = 1.5 - (length / maxBatSize)
            self.bat.body.fixtures[0].restitution = res

'''
class BatManager:
    def __init__(self, parentNode, world, renderer):
        self.world, self.field, self.renderer = world, parentNode, renderer
        self.field.setEventHandler(avg.CURSORDOWN, avg.TOUCH, self.onDown)
        self.field.setEventHandler(avg.CURSORUP, avg.TOUCH, self.onUp)
        self.reset()
        self.rec = ui.TransformRecognizer(self.field, moveHandler=self.onTransform)
        
    def reset(self):
        self.started, self.bat = False, None
        self.pos1 = self.pos2 = (0, 0)
        self.cid1 = self.cid2 = -1
    
    def onDown(self, event):
        if self.started:
            if (event.pos - self.pos1).getNorm() > maxBatSize * PPM:
                return
            if self.bat is not None:
                self.bat.destroy()
                self.bat = None
            self.pos2 = event.pos
            self.cid2 = event.cursorid
            self.bat = Bat(self.renderer, self.world, self.field, [self.pos1, self.pos2])
#            self.field.setEventCapture(self.cid1)
#            self.field.setEventCapture(self.cid2)
        else:
            self.pos1 = event.pos
            self.cid1 = event.cursorid
            self.started = True

    def onUp(self, event):
        if event.cursorid == self.cid1:                
            if self.bat is None:
                self.reset()
            else:
#                self.field.releaseEventCapture(self.cid1)
#                self.field.releaseEventCapture(self.cid2)
                self.bat.destroy()
                self.bat = None
                self.pos1 = self.pos2
                self.cid1 = self.cid2
                self.cid2 = -1
        elif event.cursorid == self.cid2:
            if self.bat is not None:
#                self.field.releaseEventCapture(self.cid1)
#                self.field.releaseEventCapture(self.cid2)
                self.bat.destroy()
                self.bat = None
                self.cid2 = -1
    
    def onTransform(self, tr):
        if self.bat is not None:
            # ugly
            vert = [(tr.scale * v[0], tr.scale * v[1]) for v in self.bat.body.fixtures[0].shape.vertices]
            pos1, pos2 = avg.Point2D(vert[0]), avg.Point2D(vert[1])
            length = (pos2 - pos1).getNorm()
            if length > maxBatSize:
                self.bat.body.active, self.bat.node.active = False, False
            else:
                self.bat.body.active, self.bat.node.active = True, True
                width = (maxBatSize - length) / 10
                self.bat.body.fixtures[0].shape.SetAsBox(length / 2, width / 2)
                self.bat.body.position = tr.pivot / PPM 
                self.bat.body.position += tr.trans / PPM
                self.bat.body.angle += tr.rot
                
                res = 1.5 - (length / maxBatSize)
                self.bat.body.fixtures[0].restitution = res
'''                
Game.start(sys.argv) # TODO decide whether to return to the previous launch mode
