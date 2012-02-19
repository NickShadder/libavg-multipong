'''
Created on 19.01.2012

@author: 2526240
'''

from libavg import avg, gameapp, statemachine, ui
from Box2D import b2World, b2EdgeShape, b2Vec2, b2FixtureDef
from gameobjects import Ball, Bat, Ghost, Player, GhostLine
from config import PPM, TIME_STEP

import random

g_player = avg.Player.get()

# XXX encapsulate this
def w2a(coords):
    return avg.Point2D(coords[0], coords[1]) * PPM
def a2w(coords):
    return b2Vec2(coords[0], coords[1]) / PPM

class Game(gameapp.GameApp):
    def init(self):
        self.machine = statemachine.StateMachine('BEMOCK', 'MainMenu')
        self.machine.addState('MainMenu', ['Playing', 'Tutorial', 'Highscore'], enterFunc=self.showMenu, leaveFunc=self.hideMenu)
        self.machine.addState('Tutorial', ['MainMenu', 'Playing', 'Tutorial'], enterFunc=self.startTutorial, leaveFunc=self.hideTutorial)
        self.machine.addState('Playing', ['Winner'], enterFunc=self.startPlaying)
        self.machine.addState('Winner', ['Playing', 'Highscore']) # XXX clarify this stuff
        self.machine.addState('Highscore', ['MainMenu'], enterFunc=self.showHighscore,leaveFunc=self.hideHighscore)        
        self.showMenu()
        
    def showMenu(self):
        # XXX make better images... maybe .svg?
        self.menuScreen = avg.DivNode(parent=self._parentNode, size=self._parentNode.size)
        def makeButton(href,posY,pyFunc):
            pre='../data/img/btn_'
            upNode = avg.ImageNode(href=pre+href+'_up.png')
            downNode = avg.ImageNode(href=pre+href+'_dn.png')
            return ui.TouchButton(upNode, downNode, clickHandler=pyFunc,
                                          parent=self.menuScreen, pos=(self.menuScreen.pivot[0] - upNode.width / 2, posY))        
        self.startButton = makeButton('start',30,lambda:self.machine.changeState('Playing')) # XXX remove hardcode  
        self.tutorialButton = makeButton('tut',200,lambda:self.machine.changeState('Tutorial')) # XXX remove hardcode  
        self.highscoreButton = makeButton('high',370,lambda:self.machine.changeState('Highscore')) # XXX remove hardcode
        self.exitButton = makeButton('exit',540,lambda:exit(0)) # XXX remove hardcode
               
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

    def showHighscore(self):
        # TODO implement highscore (note: use libavg.ui.Keyboard for user name input, use xml or ini for info storage)
        pass
    
    def hideHighscore(self):
        # TODO implement this by simply tearing down what you have built in showHighscore ;)
        pass
    
    def startPlaying(self):
        # TODO get rid of this
        self.mag_num = 0.0
        self.rand_num = random.randint(10,30)
        self.max_balls = 3
        self.changeindex = 0
        
        self.display = self._parentNode
        displayWidth = self.display.size[0]
        displayHeight = self.display.size[1]        
        
        fieldSize = (displayWidth / 3, displayHeight)
        self.field1 = avg.DivNode(parent=self.display, size=fieldSize, elementoutlinecolor='00FF00')
        self.field2 = avg.DivNode(parent=self.display, size=fieldSize, elementoutlinecolor='0000FF', pos=(displayWidth * 2 / 3, 0))
        
        self.leftPlayer, self.rightPlayer = Player(self.field1), Player(self.field2) # XXX rename into player1 and player2
        self.leftPlayer.other, self.rightPlayer.other = self.rightPlayer, self.leftPlayer # monkey patch ftw =)
        
        # TODO get rid of this
        self.leftpoints = 0
        self.ballrad = 1
        self.ghostrad = 2
        self.rightpoints = 0
        # TODO move to the Player class
        self.lpn = avg.WordsNode(parent=self.display, pos=(10, 10), text="Points: " + str(self.leftpoints), color="FF1337")
        self.rpn = avg.WordsNode(parent=self.display, pos=(displayWidth - 100, 10), text="Points: " + str(self.rightpoints), color="FF1337")
        
        # create world
        self.world = b2World(gravity=(0, 0), doSleep=True)
        # create sides
        avg.LineNode(parent=self.display, pos1=(0, 1), pos2=(displayWidth, 1))
        avg.LineNode(parent=self.display, pos1=(0, displayHeight - 1), pos2=(displayWidth, displayHeight - 1))
        
        # TODO encapsulate in a class and merge with ghostlines, should probably also create some tetrisLines
        self.static = self.world.CreateStaticBody(position=(0, 0))
        
        shape = b2EdgeShape(vertices=[a2w((0, 1)), a2w((displayWidth, 1))])
        fixture = b2FixtureDef(shape=shape, density=1, groupIndex=1)
        self.static.CreateFixture(fixture)
        
        shape = b2EdgeShape(vertices=[a2w((0, displayHeight)), a2w((displayWidth, displayHeight))])
        fixture = b2FixtureDef(shape=shape, density=1, groupIndex=1)
        self.static.CreateFixture(fixture)        
        
        # create balls
        self.startpos = a2w(self.display.size / 2)
        self.balls = [Ball(self.display, self, self.world, self.startpos, self.ballrad)]
        # start ball movement
        self.balls[0].start_moving(self.startpos);
        # create ghosts
        self.ghosts = [Ghost(self.display, self.world, (10, 10), "FF1337", 0, self.ghostrad),
                       Ghost(self.display, self.world, (10, 25), "00FF66", 0, self.ghostrad),
                       Ghost(self.display, self.world, (25, 10), "9F00CC", 0, self.ghostrad),
                       Ghost(self.display, self.world, (25, 25), "18847B", 0, self.ghostrad)]

        GhostLine(self.display, self.world, a2w((30, 0)), a2w((30, displayHeight))) 
        GhostLine(self.display, self.world, a2w((displayWidth - 60, 0)), a2w((displayWidth - 60, displayHeight)))

        
        g_player.setInterval(16, self.step) # XXX setOnFrameHandler ?
 
        BatSpawner(self.field1, self.world)
        BatSpawner(self.field2, self.world)

    # TODO move into the ghost class as ghost.move()
    
    def move_ghosts(self):
        self.changeindex = self.changeindex + 1;
        if self.changeindex > 60:
            self.changeindex = 0
            for ghost in self.ghosts:
                ghost.changedirection();        
    
    # TODO move into the ghost class as ghost.changeMortality
    def changeMortality(self):
        for ghost in self.ghosts:
            if(ghost.mortal):
                ghost.mortal = 0
                ghost.node.fillcolor = ghost.old_color
            else:
                ghost.mortal = 1
                ghost.node.fillcolor = '0000FF'
    
    # FIXME rethink concept        
    def newBall(self): 
        self.balls[0].destroy() 
        self.balls = [Ball(self.display, self, self.world, self.startpos, self.ballrad)] 
        self.balls[0].start_moving(self.startpos)
        
    # FIXME rethink concept        
    def addBall(self):
        if(len(self.balls) < (self.max_balls)):
            self.balls.append(Ball(self.display, self, self.world, self.startpos, self.ballrad))
            self.balls[-1].start_moving(self.startpos)
    
    
    def newGhost(self, index): 
        color = self.ghosts[index].old_color 
        self.ghosts[index].destroy() 
        del self.ghosts[index] 
        self.ghosts.append(Ghost(self.display, self.world, (random.randint(10, 30), random.randint(10, 30)), color, 0, self.ghostrad))
        self.addBall()
    
    # TODO replace by a collisionlistener
    def checkGhostForBorder(self):
        for ghost in self.ghosts:
            if ghost.body.position[0] < 10:
                ghost.setDir("left")
            elif ghost.body.position[0] > 60:
                ghost.setDir("right")
         
    def step(self): 
        self.renderjob() 
        self.checkballposition() # XXX get rid of this call 
        self.move_ghosts()
        self.checkforballghost() # XXX get rid of this call
        # TODO get this out of here
        if((self.mag_num / 1) >= self.rand_num):
            self.changeMortality()
            self.mag_num = 0.0
            self.rand_num = random.randint(10, 30)
        else:
            self.mag_num = self.mag_num + 0.16

    # TODO move this into an own class
    def renderjob(self):
        self.world.Step(TIME_STEP, 10, 10)
        self.world.ClearForces()
        for body in self.world.bodies:
            if body.userData is not None:
                for fixture in body.fixtures:
                    if body.userData['type'] == 'poly':
                        vertices = [(body.transform * v) for v in fixture.shape.vertices]
                        vertices = [w2a(v) for v in vertices]
                        node = body.userData['node']
                        vertices = [node.getRelPos(v) for v in vertices]
                        node.pos = vertices
                    elif body.userData['type'] == 'body':
                        body.userData['node'].r = fixture.shape.radius * PPM
                        position = body.transform * fixture.shape.pos
                        body.userData['node'].pos = w2a(position)
                    elif body.userData['type'] == 'line':
                        vertices = [body.transform * v for v in fixture.shape.vertices]
                        vertices = [w2a(v) for v in vertices]
                        body.userData['node'].pos1 = vertices[0]
                        body.userData['node'].pos2 = vertices[1]
                    elif body.userData['type'] == 'div':
                        print body
                        print body.position
                        print body.angle
    
    # TODO replace by a collisionlistener
    def checkforballghost(self):  
        index = 0    
        for ghost in self.ghosts:  
            if (ghost.body.position[0] - self.balls[0].body.position[0] < 3 and  
            ghost.body.position[0] - self.balls[0].body.position[0] > -3 and   
            ghost.body.position[1] - self.balls[0].body.position[1] < 3 and  
            ghost.body.position[1] - self.balls[0].body.position[1] > -3 and ghost.mortal == 0  
            ):  
                self.newBall() 
                 
            if (ghost.body.position[0] - self.balls[0].body.position[0] < 3 and  
            ghost.body.position[0] - self.balls[0].body.position[0] > -3 and   
            ghost.body.position[1] - self.balls[0].body.position[1] < 3 and  
            ghost.body.position[1] - self.balls[0].body.position[1] > -3 and ghost.mortal == 1  
            ):  
                self.newGhost(index) 
                #Player Punkte addieren 
            index += 1

    # TODO replace by a collisionlistener
    def checkballposition(self): 
        for ball in self.balls: 
            if ball.body.position[0] > (self.display.size[0] / PPM - 1) + self.ballrad: 
                self.balls[0].destroy() 
                self.balls = [Ball(self.display, self, self.world, self.startpos, self.ballrad)] 
                #ball.body.position = self.startpos 
                 
                self.leftPlayer.addPoint() 
                self.lpn.text = "Points: " + str(self.leftPlayer.points) 
                 
                self.balls[0].start_moving(self.startpos)
            elif ball.body.position[0] < (-1) * self.ballrad: 
                self.balls[0].destroy() 
                self.balls = [Ball(self.display, self, self.world, self.startpos, self.ballrad)] 
                #ball.body.position = self.startpos 
                self.rightPlayer.addPoint() 
                self.rpn.text = "Points: " + str(self.rightPlayer.points) 
                self.balls[0].start_moving(self.startpos)
    
class BatSpawner:
    def __init__(self, parentNode, world):
        self.world = world
        self.field = parentNode
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
            self.bat = Bat(self.field, self.world, self.pos1, self.pos2)
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
