'''
Created on 19.01.2012

@author: 2526240
'''
import sys,random
from libavg import avg, gameapp, statemachine, ui
from Box2D import b2World, b2Vec2, b2ContactListener
from gameobjects import Ball, Bat, Ghost, Player, BorderLine, Block, PersistentBonus
from config import PPM, TIME_STEP, maxBalls, ballRadius, maxBatSize

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
    def __init__(self,hitset):
        b2ContactListener.__init__(self)
        self.hitset = hitset
    def EndContact(self, contact):
        fA, fB = contact.fixtureA, contact.fixtureB
        dA, dB = fA.userData, fB.userData
        ball, brick = None, None
        if dA == 'ball' and dB == 'brick':
            ball, brick = fA.body.userData, fB.body.userData
        elif dA == 'brick' and dB == 'ball':
            brick, ball = fA.body.userData, fB.body.userData
        if brick and ball:
            self.hitset.add(brick)
        
    def PreSolve(self, contact, oldManifold):
        fA, fB = contact.fixtureA, contact.fixtureB
        dA, dB = fA.userData, fB.userData
        ball, bat = None, None
        if dA == 'ball' and dB == 'bat':
            ball, bat = fA.body.userData, fB.body.userData
        elif dA == 'bat' and dB == 'ball':
            bat, ball = fA.body.userData, fB.body.userData
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
        height = node.height / 8 # XXX make dependant on actual resolution sometime
        size = (height * 2.4, height)
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
        avg.WordsNode(parent=self.aboutScreen, x=5, text='Unnamed Multipong<br/>as envisioned and implemented by<br/>Benjamin Guttman<br/>Joachim Couturier<br/>Philipp Hermann<br/>Mykola Havrikov<br/><br/>This game uses libavg(www.libavg.de) and PyBox2D(http://code.google.com/p/pybox2d/)')
        self.menuButton = self.makeButtonInMiddle('menu', self.aboutScreen, 1, lambda:self.machine.changeState('MainMenu'))

    def hideAbout(self):
        self.aboutScreen.unlink(True)
        self.aboutScreen = None

    def startPlaying(self):
        # libavg setup
        self.display = avg.DivNode(parent=self._parentNode, size=self._parentNode.size)
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
        self.mainLoop = g_player.setInterval(13, self.step) # XXX g_player.setOnFrameHandler(self.step) 
        
        # pybox2d setup
        self.world = b2World(gravity=(0, 0), doSleep=True)
        self.hitset = set()
        self.listener = ContactListener(self.hitset)
        self.world.contactListener = self.listener
        BorderLine(self.world, a2w((0, 1)), a2w((displayWidth, 1)),1)
        BorderLine(self.world, a2w((0, displayHeight)), a2w((displayWidth, displayHeight)),1)
        BorderLine(self.world, a2w((30, 0)), a2w((30, displayHeight)), 1, False, 'ball') # XXX remove hardcode 
        BorderLine(self.world, a2w((displayWidth - 30, 0)), a2w((displayWidth - 30, displayHeight)), 1, False, 'ball') # XXX remove hardcode
        
        # game setup
        # create ghosts                                        XXX remove hardcode
        self.ghosts = [Ghost(self.renderer, self.world, self.display, (23, 10), "blinky"),
                       Ghost(self.renderer, self.world, self.display, (40, 10), "pinky"),
                       Ghost(self.renderer, self.world, self.display, (23, 40), "inky"),
                       Ghost(self.renderer, self.world, self.display, (40, 40), "clyde")]
        
        
        # create balls
        self.startpos = a2w(self.display.pivot) # TODO remove this
        self.balls = [Ball(self.renderer, self.world, self.display, self.startpos, self.leftPlayer, self.rightPlayer)]

        BatManager(self.field1, self.world, self.renderer)
        BatManager(self.field2, self.world, self.renderer)
        
        # g_player.setTimeout(1000,self.bonusJob) # TODO reenable
        
        # TEST ORGY
#        Block(self.display, self.renderer, self.world, (5, 5), (self.leftPlayer, self.rightPlayer), Block.form['SINGLE'])
#        #Block(self.display, self.renderer, self.world, (5, 50), (self.leftPlayer, self.rightPlayer), Block.form['DOUBLE'])
#        #Block(self.display, self.renderer, self.world, (widthThird + 10, 200), (self.leftPlayer, self.rightPlayer), Block.form['TRIPLE'])
#        Block(self.display, self.renderer, self.world, (5, 150), (self.leftPlayer, self.rightPlayer), Block.form['EDGE'])
#        #Block(self.display, self.renderer, self.world, (widthThird + 20, 400), (self.leftPlayer, self.rightPlayer), Block.form['SQUARE'])
#        #Block(self.display, self.renderer, self.world, (5, 250), (self.leftPlayer, self.rightPlayer), Block.form['LINE'])
#        #Block(self.display, self.renderer, self.world, (5, 350), (self.leftPlayer, self.rightPlayer), Block.form['SPIECE'])
#        Block(self.display, self.renderer, self.world, (displayWidth - widthThird + 10, 200), (self.leftPlayer, self.rightPlayer), Block.form['DOUBLE'])
#        Block(self.display, self.renderer, self.world, (displayWidth - widthThird + 20, 400), (self.leftPlayer, self.rightPlayer), Block.form['TPIECE'])
    
    def bonusJob(self):
        PersistentBonus(self.display,self,self.world,random.choice(PersistentBonus.boni.items()))
        # the timeout must not be shorter than config.bonusTime
        # TODO get the bonusTime out of the config and out of the user's control 
        g_player.setTimeout(random.choice([3000,4000,5000]),self.bonusJob)

    def win(self, player):
        g_player.clearInterval(self.mainLoop)
        # TODO tear down world and current display
        # TODO show winner/revanche screen
      
    def addBall(self):
        if len(self.balls) < maxBalls:
            self.balls.append(Ball(self.renderer, self.world, self.display, self.startpos, self.leftPlayer, self.rightPlayer))
    
    def removeBall(self, ball):
        self.balls.remove(ball)
        ball.destroy()


    def _processBallvsBrick(self,hitset):
        for brick in hitset:
            brick.hit()
        hitset.clear()
        
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
                        if player is not None:
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
                                        
    def step(self):
        self.world.Step(TIME_STEP, 10, 10)
        self.world.ClearForces()
        self._processBallvsBrick(self.hitset)
        self._processBallvsGhost()
        self._checkBallPosition()
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
        self.field.setEventHandler(avg.CURSORUP, avg.TOUCH, self.onUp)
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
            assert len(self.pos) == 1
            self.machine.changeState('started')
        elif state == 'started':
            assert len(self.pos) == 1
            if (e.pos - self.pos[0][1]).getNorm() <= maxBatSize * PPM:
                self.pos.append((e.cursorid, e.pos))
                assert len(self.pos) == 2
                self.machine.changeState('created')

    def onUp(self, e):
        state = self.machine.state
        cid = e.cursorid
        if state == 'started':
            assert len(self.pos) == 1
            if cid == self.pos[0][0]:
                self.machine.changeState('idle')
        elif state == 'created':
            assert len(self.pos) == 2            
            if cid == self.pos[1][0]:
                del self.pos[1]
                assert len(self.pos) == 1
                self.machine.changeState('started')
            elif cid == self.pos[0][0]:
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
            width = max(1/PPM,(maxBatSize - length) / 10)
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
