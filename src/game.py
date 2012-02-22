'''
Created on 19.01.2012

@author: 2526240
'''
import sys
from libavg import avg, gameapp, statemachine, ui
from Box2D import b2World, b2Vec2, b2ContactListener
from gameobjects import Ball, Bat, Ghost, Player, BorderLine
from config import PPM, TIME_STEP, maxBalls, ballRadius

import random

g_player = avg.Player.get()

def w2a(coords):
    return avg.Point2D(coords[0], coords[1]) * PPM
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
        # TODO implement ausrichtung in flugrichting
        for obj in self.objects:
            body = obj.body
            for fixture in body.fixtures:
                if body.userData['type'] == 'body':
                    position = body.transform * fixture.shape.pos
                    body.userData['node'].pos = w2a(position) - body.userData['node'].size / 2
                    body.userData['node'].angle = body.angle
                    break # XXX solve this code smell by convention
                elif body.userData['type'] == 'poly': # XXX get rid of this after Bat reimplementation
                    vertices = [(body.transform * v) for v in fixture.shape.vertices]
                    vertices = [w2a(v) for v in vertices]
                    node = body.userData['node']
                    vertices = [node.getRelPos(v) for v in vertices]
                    node.pos = vertices

class ContactListener(b2ContactListener):
    def __init__(self):
        b2ContactListener.__init__(self)
    def BeginContact(self, contact):
        pass
    def PreSolve(self, contact, oldManifold):
        fA, fB = contact.fixtureA, contact.fixtureB
        dA, dB = fA.userData, fB.userData
        ball, bat = None, None
        if dA == 'ball' and dB == 'bat':
            ball, bat = fA.body.userData['obj'], fB.body.userData['obj']
        elif dA == 'bat' and dB == 'ball':
            bat, ball = fA.body.userData['obj'], fB.body.userData['obj']
        if bat and ball:
            ball.lastPlayer = bat.zone.player
            
class Game(gameapp.GameApp):
    def init(self):
        self.machine = statemachine.StateMachine('BEMOCK', 'MainMenu')
        self.machine.addState('MainMenu', ['Playing', 'Tutorial', 'About'], enterFunc=self.showMenu, leaveFunc=self.hideMenu)
        self.machine.addState('Tutorial', ['MainMenu', 'Playing', 'Tutorial'], enterFunc=self.startTutorial, leaveFunc=self.hideTutorial)
        self.machine.addState('Playing', ['Winner'], enterFunc=self.startPlaying)
        self.machine.addState('Winner', ['Playing', 'MainMenu']) # XXX clarify this stuff
        self.machine.addState('About', ['MainMenu'], enterFunc=self.showAbout, leaveFunc=self.hideAbout)        
        self.showMenu()
        
    def makeButtonInMiddle(self, name, node, yOffset, pyFunc):
        path = '../data/img/btn/'
        svg = avg.SVG(path + name + '_up.svg', False)
        width = node.width / 5 #                     XXX maybe start with height
        size = (width, width / 2.4)
        upNode = svg.createImageNode('layer1', {}, size)
        svg = avg.SVG(path + name + '_dn.svg', False)
        downNode = svg.createImageNode('layer1', {}, size)
        position = (node.pivot[0] - upNode.width / 2, node.pivot[1] + yOffset * upNode.height + yOffset * 50)
        return ui.TouchButton(upNode, downNode, clickHandler=pyFunc, parent=node, pos=position)
            
    def showMenu(self):
        self.menuScreen = avg.DivNode(parent=self._parentNode, size=self._parentNode.size)
        self.startButton = self.makeButtonInMiddle('start', self.menuScreen, -1, lambda:self.machine.changeState('Playing'))
        self.tutorialButton = self.makeButtonInMiddle('help', self.menuScreen, 0, lambda:self.machine.changeState('Tutorial'))
        self.aboutButton = self.makeButtonInMiddle('about', self.menuScreen, 1, lambda:self.machine.changeState('About'))
        self.exitButton = self.makeButtonInMiddle('exit', self.menuScreen, 2, lambda:exit(0))

    def hideMenu(self):
        # XXX find out if we need to tear down all the buttons first
        self.menuScreen.unlink(True)
        self.menuScreen = None
    
    def startTutorial(self):
        # TODO implement a tutorial sequence using avg only - no need to use pybox2d for simple animations 
        pass
    
    def hideTutorial(self):
        # TODO implement this by simply tearing down what you have built in startTutorial ;)
        pass
    
    def showAbout(self):
        self.aboutScreen = avg.DivNode(parent=self._parentNode, size=self._parentNode.size)
        avg.WordsNode(parent=self.aboutScreen, x=5, text='Unnamed Multipong<br/>as envisioned and implemented by<br/>Benjamin Guttman<br/>Joachim Couturier<br/>Phillip Hermann<br/>Mykola Havrikov<br/><br/>This game uses libavg(www.libavg.de) and PyBox2D(http://code.google.com/p/pybox2d/)')
        self.menuButton = self.makeButtonInMiddle('menu', self.aboutScreen, 1, lambda:self.machine.changeState('MainMenu'))
    
    def hideAbout(self):
        self.aboutScreen.unlink(True)
        self.aboutScreen = None
    
    def startPlaying(self):
        # TODO get rid of this
        self.mag_num = 0.0
        self.rand_num = random.randint(10, 30)
        self.changeindex = 0
        # libavg setup
        self.display = self._parentNode
        self.display.player = None # monkey patch
        (displayWidth, displayHeight) = self.display.size
        widthThird = displayWidth / 3
        fieldSize = (widthThird, displayHeight)
        self.field1 = avg.DivNode(parent=self.display, size=fieldSize)
        self.field2 = avg.DivNode(parent=self.display, size=fieldSize, pos=(displayWidth - widthThird, 0))
        
        self.leftPlayer, self.rightPlayer = Player(self, self.field1), Player(self, self.field2)
        self.leftPlayer.other, self.rightPlayer.other = self.rightPlayer, self.leftPlayer # monkey patch ftw =)
        
        avg.LineNode(parent=self.display, pos1=(0, 1), pos2=(displayWidth, 1))
        avg.LineNode(parent=self.display, pos1=(0, displayHeight), pos2=(displayWidth, displayHeight))
        svg = avg.SVG('../data/img/btn/dotted_line.svg', False)
        svg.createImageNode('layer1', dict(parent=self.display, pos=(widthThird, 0)), (2, displayHeight))
        svg.createImageNode('layer1', dict(parent=self.display, pos=(displayWidth - widthThird, 0)), (2, displayHeight))
        
        self.renderer = Renderer()
        self.mainLoop = g_player.setInterval(16, self.step) # XXX setOnFrameHandler ?
        
        # pybox2d setup
        self.world = b2World(gravity=(0, 0), doSleep=True)
        self.listener = ContactListener()        
        self.world.contactListener = self.listener        
        BorderLine(self.world, a2w((0, 1)), a2w((displayWidth, 1)), ['ghost', 'ball'])
        BorderLine(self.world, a2w((0, displayHeight)), a2w((displayWidth, displayHeight)), ['ghost', 'ball'])
        BorderLine(self.world, a2w((30, 0)), a2w((30, displayHeight)), ['ghost']) # XXX remove hardcode 
        BorderLine(self.world, a2w((displayWidth - 30, 0)), a2w((displayWidth - 30, displayHeight)), ['ghost']) # XXX remove hardcode
        
        # game setup
        
        # create ghosts                                        XXX remove hardcode
        self.ghosts = [Ghost(self.renderer, self.world, self.display, (23, 10), "blinky"),
                       Ghost(self.renderer, self.world, self.display, (40, 10), "pinky"),
                       Ghost(self.renderer, self.world, self.display, (23, 40), "inky"),
                       Ghost(self.renderer, self.world, self.display, (40, 40), "clyde")]
        # create balls
        self.startpos = a2w(self.display.pivot) # TODO remove this
        self.balls = [Ball(self.renderer, self.world, self.display, self.startpos, self.leftPlayer, self.rightPlayer)]
                         
        BatSpawner(self.field1, self.world, self.renderer)
        BatSpawner(self.field2, self.world, self.renderer)
                
    def win(self, player):
        g_player.clearInterval(self.mainLoop)
        # TODO tear down world and current display
        # TODO show winner/revanche screen

    def move_ghosts(self):
        self.changeindex = self.changeindex + 1
        if self.changeindex > 60:
            self.changeindex = 0
            for ghost in self.ghosts:
                ghost.changedirection()        
    
    # TODO move into the ghost class as ghost.changeMortality or ghost.flipState
    def changeMortality(self):
        for ghost in self.ghosts:
            ghost.flipState()
    
    # FIXME rethink concept        
    def addBall(self):
        if(len(self.balls) < (maxBalls)):
            self.balls.append(Ball(self.renderer, self.world, self.display, self.startpos))
            self.balls[-1].nudge(self.startpos)
    
    def newGhost(self, index): 
        name = self.ghosts[index].name
        self.ghosts[index].destroy() 
        del self.ghosts[index] 
        self.ghosts.append(Ghost(self.renderer, self.world, self.display, (random.randint(10, 30), random.randint(10, 30)), name))
        self.addBall()
        
    def processBallCollisions(self):
        killSet = set()
        for ball in self.balls:
            for ce in ball.body.contacts:
                contact = ce.contact
                ghost = None
                if contact.fixtureA.userData == 'ghost':
                    ghost = contact.fixtureA.body.userData['obj']
                elif contact.fixtureB.userData == 'ghost':
                    ghost = contact.fixtureB.body.userData['obj']                
                if ghost is not None:
                    if ghost.mortal:
                        # ball eats ghost
                        if ball.lastPlayer is not None and ghost not in killSet: # ghost has two shapes! 
                            ball.lastPlayer.addPoint()
                        killSet.add(ghost)
                    else:
                        # ghost eats ball
                        player = ball.zoneOfPlayer()
                        if player is not None and ball not in killSet:
                            player.removePoint()
                        killSet.add(ball)
        for obj in killSet:
            obj.reSpawn() # duck typing ftw :)
               
    def step(self):
        self.world.Step(TIME_STEP, 10, 10)
        self.world.ClearForces()
        self.processBallCollisions()
        self.checkballposition() # XXX get rid of this call 
        self.move_ghosts() # XXX solve better
        # TODO get this out of here
        if((self.mag_num / 1) >= self.rand_num):
            self.changeMortality()
            self.mag_num = 0.0
            self.rand_num = random.randint(10, 30)
        else:
            self.mag_num = self.mag_num + 0.16            
        # draw world    
        self.renderer.draw()

    # TODO replace by a collisionlistener
    def checkballposition(self):
        for ball in self.balls: 
            if ball.body.position[0] > (self.display.size[0] / PPM - 1) + ballRadius: 
                self.leftPlayer.addPoint()
                self.balls[0].reSpawn()                
            elif ball.body.position[0] < (-1) * ballRadius: 
                self.rightPlayer.addPoint()
                self.balls[0].reSpawn()

# XXX rename class
class BatSpawner:
    def __init__(self, parentNode, world, renderer):
        self.world = world
        self.field = parentNode
        self.renderer = renderer
        self.field.setEventHandler(avg.CURSORDOWN, avg.TOUCH, self.onDetect)
        #self.field.setEventHandler(avg.CURSORMOTION,avg.TOUCH,self.onMove) # TODO solve with transformhandler on bat itself
        self.field.setEventHandler(avg.CURSORUP, avg.TOUCH, self.onUp)
        self.detected = False
        self.bat = None
        self.pos1 = (0, 0)
        self.pos2 = (0, 0)
    
    def onDetect(self, event):
        if self.detected:
            if self.bat is not None:
                self.bat.destroy()
                self.bat = None
            self.pos2 = event.pos
            self.bat = Bat(self.renderer, self.world, self.field, self.pos1, self.pos2)
        else:
            self.pos1 = event.pos
            self.detected = True

    def onUp(self, event):
        self.detected = False
        if self.bat is not None:
            self.bat.destroy()
            self.bat = None
    
    '''        
    def onMove(self, event):
        if event.cursorid == self.cid1 and self.bat is not None:
            self.pos1 = a2w(self.field.getRelPos(event.pos))           
            self.bat.update1(self.pos1)
        elif event.cursorid == self.cid2 and self.bat is not None:
            self.pos2 = a2w(self.field.getRelPos(event.pos))
            self.bat.update2(self.pos2)
            
    def angle(self):
        vec = self.pos2 - self.pos1
        ang = math.atan2(vec.y, vec.x)
        if ang < 0:
            ang += math.pi * 2
        return ang
    '''

Game.start(sys.argv) # TODO decide whether to return to the previous launch mode
