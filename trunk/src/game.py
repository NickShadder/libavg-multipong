'''
Created on 19.01.2012

@author: 2526240
'''

from libavg import avg, gameapp
from Box2D import b2World, b2EdgeShape, b2Vec2, b2FixtureDef
from gameobjects import Ball, Bat, Ghost, Player, GhostLine
from config import PPM, TIME_STEP

import random


g_player = avg.Player.get() # globally store the avg player

def w2a(coords):
    return avg.Point2D(coords[0], coords[1]) * PPM
def a2w(coords):
    return b2Vec2(coords[0], coords[1]) / PPM

class Game(gameapp.GameApp):
    def init(self):
        self.mag_num = 0.0
        self.rand_num = random.randint(10,30)
        self.max_balls = 3
        # setup overall display 
        self.changeindex = 0
        self.display = self._parentNode
        self.display.elementoutlinecolor = 'FF0000'
        # store some values
        self.displayWidth = self.display.size[0]
        self.displayHeight = self.display.size[1]        
        # initialize values
        self.leftpoints = 0
        self.ballrad = 1
        self.rightpoints = 0
        # points 
        self.lpn = avg.WordsNode(parent=self.display, pos=(10, 10), text="Points: " + str(self.leftpoints), color="FF1337")
        self.rpn = avg.WordsNode(parent=self.display, pos=(self.displayWidth - 100, 10), text="Points: " + str(self.rightpoints), color="FF1337")
        # setup player fields
        fieldSize = (self.displayWidth / 3, self.displayHeight)
        self.field1 = avg.DivNode(parent=self.display, size=fieldSize, elementoutlinecolor='00FF00')
        self.field2 = avg.DivNode(parent=self.display, size=fieldSize, elementoutlinecolor='0000FF', pos=(self.displayWidth * 2 / 3, 0))
        # create world
        self.world = b2World(gravity=(0, 0), doSleep=True)
        # create sides
        avg.LineNode(parent=self.display, pos1=(0, 1), pos2=(self.displayWidth, 1))
        avg.LineNode(parent=self.display, pos1=(0, self.displayHeight - 1), pos2=(self.displayWidth, self.displayHeight - 1))
        
        self.static = self.world.CreateStaticBody(position=(0, 0))
        
        shape = b2EdgeShape(vertices=[a2w((0, 1)), a2w((self.displayWidth, 1))])
        fixture = b2FixtureDef(shape=shape, density=1,groupIndex=1)
        self.static.CreateFixture(fixture)
        
        shape = b2EdgeShape(vertices=[a2w((0, self.displayHeight)), a2w((self.displayWidth, self.displayHeight))])
        fixture = b2FixtureDef(shape=shape, density=1,groupIndex=1)
        self.static.CreateFixture(fixture)        
        
        # create balls
        self.startpos = a2w(self.display.size / 2)
        self.balls = [Ball(self.display, self, self.world, self.startpos, self.ballrad)]
        # start ball movement
        self.balls[0].start_moving(self.startpos);
        # create ghosts
        self.ghosts = [Ghost(self.display, self.world, (10, 10), "FF1337",0 , 1),
                       Ghost(self.display, self.world, (10, 25), "00FF66",0 ,1),
                       Ghost(self.display, self.world, (25, 10), "9F00CC",0 ,1),
                       Ghost(self.display, self.world, (25, 25), "4542CE",0 ,1)]

        GhostLine(self.display, self.world, a2w((30, 0)), a2w((30, self.displayHeight))) 
        GhostLine(self.display, self.world, a2w((self.displayWidth - 60, 0)), a2w((self.displayWidth - 60, self.displayHeight)))

        
                
    # setup drawing of the world
        g_player.setInterval(16, self.step) # TODO setOnFrameHanlder?

    #player
        self.leftPlayer = Player()
        self.rightPlayer = Player()
    # bat handler1 
        s1 = BatSpawner(self.field1, self.world)
        s2 = BatSpawner(self.field2, self.world)

    def move_ghosts(self):
        self.changeindex = self.changeindex + 1;
        if self.changeindex > 60:
            self.changeindex = 0
            for ghost in self.ghosts:
                ghost.changedirection();
                
    def changeMortality(self):
        for ghost in self.ghosts:
            if(ghost.mortal):
                ghost.mortal = 0
                ghost.node.fillcolor = ghost.old_color
            else:
                ghost.mortal = 1
                ghost.node.fillcolor = '0000FF'
            
    def newBall(self,index):
        if(len(self.balls) > 1):
            self.balls[index].destroy()
            del self.balls[index]
        else:
            self.balls[0].destroy()
            self.balls = [Ball(self.display, self, self.world, self.startpos, self.ballrad)]
            self.balls[0].start_moving(self.startpos);
        
    def addBall(self):
        if(len(self.balls) < (self.max_balls)):
            self.balls.append(Ball(self.display, self, self.world, self.startpos, self.ballrad))
            self.balls[-1].start_moving(self.startpos);
        
    def newGhost(self,index):
        color = self.ghosts[index].color
        self.ghosts[index].destroy()
        del self.ghosts[index]
        self.ghosts.append(Ghost(self.display, self.world, (random.randint(10,30),random.randint(10,30)),color,1 ,1))
        self.addBall()
    
    def checkGhostForBorder(self):
        for ghost in self.ghosts:
            if ghost.body.position[0] < 10:
                ghost.setDir("left")
            elif ghost.body.position[0] > 60:
                ghost.setDir("right")
                
    def checkballposition(self):
        for ball in self.balls:
            if ball.body.position[0] > (self.displayWidth / PPM - 1) + self.ballrad:
                if(len(self.balls) > 1):
                    self.balls[self.balls.index(ball)].destroy()
                    del self.balls[self.balls.index(ball)]
                else:
                    self.balls[0].destroy()
                    self.balls = [Ball(self.display, self, self.world, self.startpos, self.ballrad)]
                    #ball.body.position = self.startpos
                
                self.leftPlayer.addPoint()
                self.lpn.text = "Points: " + str(self.leftPlayer.getPoints())
                
                self.balls[0].start_moving(self.startpos);
            elif ball.body.position[0] < (-1) * self.ballrad:
                if(len(self.balls) > 1):
                    self.balls[self.balls.index(ball)].destroy()
                    del self.balls[self.balls.index(ball)]
                else:
                    self.balls[0].destroy()
                    self.balls = [Ball(self.display, self, self.world, self.startpos, self.ballrad)]
                #ball.body.position = self.startpos
                self.rightPlayer.addPoint()
                self.rpn.text = "Points: " + str(self.rightPlayer.getPoints())
                self.balls[0].start_moving(self.startpos);
         
    def step(self): 
        self.renderjob() 
        self.checkballposition() 
        self.move_ghosts()
        self.checkforballghost()       
        if((self.mag_num/1) >= self.rand_num):
            self.changeMortality()
            self.mag_num = 0.0
            self.rand_num = random.randint(10,30)
        else:
            self.mag_num = self.mag_num + 0.16

            
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
        
    def checkforballghost(self): 
            for ball in self.balls:
                i = self.balls.index(ball)
                index = 0
                for ghost in self.ghosts:
                    if (ghost.body.position[0] - self.balls[i].body.position[0] < 2 and 
                        ghost.body.position[0] - self.balls[i].body.position[0] > -2 and  
                        ghost.body.position[1] - self.balls[i].body.position[1] < 2 and 
                        ghost.body.position[1] - self.balls[i].body.position[1] > -2 and ghost.mortal == 0 
                        ): 
                            #print self.balls.index(self.balls[0])
                            #eventuell Fehlerquelle dann index in Variable hochzaehlen
                            #self.newBall(self.balls.index(ball))
                            self.newBall(i)
                            
                    if (ghost.body.position[0] - self.balls[i].body.position[0] < 2 and 
                        ghost.body.position[0] - self.balls[i].body.position[0] > -2 and  
                        ghost.body.position[1] - self.balls[i].body.position[1] < 2 and 
                        ghost.body.position[1] - self.balls[i].body.position[1] > -2 and ghost.mortal == 1 
                        ): 
                
                            self.newGhost(index)
                            #insert newBall
                            #Player Punkte addieren
                    index += 1
                i += 1
            '''
            index = 0   
            for ghost in self.ghosts: 
                if (ghost.body.position[0] - self.balls[0].body.position[0] < 2 and 
                ghost.body.position[0] - self.balls[0].body.position[0] > -2 and  
                ghost.body.position[1] - self.balls[0].body.position[1] < 2 and 
                ghost.body.position[1] - self.balls[0].body.position[1] > -2 and ghost.mortal == 0 
                ): 
                    #print self.balls.index(self.balls[0])
                    self.newBall(i)
                    
                if (ghost.body.position[0] - self.balls[0].body.position[0] < 2 and 
                ghost.body.position[0] - self.balls[0].body.position[0] > -2 and  
                ghost.body.position[1] - self.balls[0].body.position[1] < 2 and 
                ghost.body.position[1] - self.balls[0].body.position[1] > -2 and ghost.mortal == 1 
                ): 
                
                    self.newGhost(index)
                    #insert newBall
                    #Player Punkte addieren
                index += 1
      '''
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
            #self.pos2 = self.field.getRelPos(event.pos)
            self.pos2 = event.pos
            self.bat = Bat(self.field, self.world, self.pos1, self.pos2)
        else:
            #self.pos1 = self.field.getRelPos(event.pos)
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
