'''
Created on 19.01.2012

@author: 2526240
'''

import math
from libavg import avg,gameapp,ui
from Box2D import b2World,b2EdgeShape,b2Vec2
from gameobjects import Ball,Bat,Ghost,Player


g_player = avg.Player.get() # globally store the avg player
PPM=20.0 # pixels per meter
TARGET_FPS=60
TIME_STEP=1.0/TARGET_FPS

def w2a(coords):
    return avg.Point2D(coords[0],coords[1])*PPM
def a2w(coords):
    return b2Vec2(coords[0],coords[1])/PPM

class Game(gameapp.GameApp):
    def found(self,event):
        print "Event detected: ",event
        
    def init(self):        
    # libavg setup
        # setup overall display 
        self.display=self._parentNode
        self.display.elementoutlinecolor='FF0000'
        # store some values
        displayWidth = self.display.size[0]
        displayHeight = self.display.size[1]        
        
        self.leftpoints = 0
        self.rightpoints = 0  
          
        self.w = displayWidth
        self.h = displayHeight
        
        self.lpn = avg.WordsNode(parent=self.display,pos=(10,10),text= "Points: "+ str(self.leftpoints),color = "FF1337")
        self.rpn = avg.WordsNode(parent=self.display,pos=(self.w-100,10),text= "Points: "+ str(self.rightpoints),color = "FF1337")
      
        
        # setup player fields
        fieldSize = (displayWidth/3,displayHeight)
        self.field1 = avg.DivNode(parent=self.display,size=fieldSize,elementoutlinecolor='00FF00')
        self.field2 = avg.DivNode(parent=self.display,size=fieldSize,elementoutlinecolor='0000FF',pos=(displayWidth*2/3,0))
        # setup bat handlers
        #self.bathandler1 = ui.TransformRecognizer(self.field1, self.display, eventSource=avg.TOUCH, moveHandler=self.found)
    
    # pybox2d setup
        # create world
        self.world=b2World(gravity=(0,0),doSleep=True)
                
        # create sides
        upperBound = avg.LineNode(parent=self.display,pos1=(0,1),pos2=(displayWidth,1))
        lowerBound = avg.LineNode(parent=self.display,pos1=(0,displayHeight-1),pos2=(displayWidth,displayHeight-1))
        d = {'type':'line','node':upperBound}
        self.world.CreateStaticBody(userData=d,position=a2w((0,1)),shapes=b2EdgeShape(vertices=[a2w((0,1)),a2w((displayWidth,1))]))
        d['node']=lowerBound
        self.world.CreateStaticBody(userData=d,position=a2w((0,1)),shapes=b2EdgeShape(vertices=[a2w((0,displayHeight-1)),a2w((displayWidth,displayHeight-1))]))
                        
        # create balls
        self.startpos = a2w((displayWidth/2,displayHeight/2))
        self.balls=[Ball(self.display,self,self.world,self.startpos,1)]
        self.balls[0].start_moving(self.startpos);
#       self.ghosts = [
#                       Ghost(self.display,self.world,(10,10),"FF1337",1),
#                       Ghost(self.display,self.world,(10,25),"00FF66",1),
#                       Ghost(self.display,self.world,(25,10),"9F00CC",1),
#                       Ghost(self.display,self.world,(25,25),"4542CE",1)
#                       ]
#        
       # self.balls[1].circle.ApplyForce(force=(1500,0), point=(10,10))
        #self.balls[1].circle.ApplyForce(force=(0,0), point=(10,10))   
        # experimental bats
        
       # bat = Bat(self.display,self.world,(0,0),a2w((0,displayHeight-1))) 
       # bat2 = Bat(self.display,self.world,(a2w((displayWidth-40,0))),a2w((displayWidth-40,displayHeight-1)))
        
    # setup drawing of the world
        g_player.setInterval(16,self.step) # TODO setOnFrameHanlder?

    #player
        self.leftPlayer = Player()
        self.rightPlayer = Player()
    # bat handler1 
        s1 = BatSpawner(self.field1, self.world)
        s2 = BatSpawner(self.field2, self.world)

    def move_ghosts(self):
        for ghost in self.ghosts:
            ghost.changedirection();
            
    def newBall(self):
        self.balls[0].destroy()
        self.balls=[Ball(self.display,self,self.world,self.startpos,1)]
        self.balls[0].start_moving(self.startpos);
                
    def checkballposition(self):
        for ball in self.balls:
            if ball.circle.position[0] > (self.w/20-1)+20:
                self.balls[0].destroy()
                self.balls=[Ball(self.display,self,self.world,self.startpos,1)]
                #ball.circle.position = self.startpos
                
                self.rightPlayer.addPoint()
                self.rpn.text = "Points: " + str(self.rightPlayer.getPoints())
                self.balls[0].start_moving(self.startpos);
            elif ball.circle.position[0] < 0:
                self.balls[0].destroy()
                self.balls=[Ball(self.display,self,self.world,self.startpos,1)]
                #ball.circle.position = self.startpos
                self.leftPlayer.addPoint()
                self.lpn.text = "Points: " + str(self.leftPlayer.getPoints())
                self.balls[0].start_moving(self.startpos);
         
    def step(self):
        self.renderjob()
        self.checkballposition()
        
    def renderjob(self):
        self.world.Step(TIME_STEP, 10, 10)
        for body in self.world.bodies:  # inefficient
            # The body gives us the position and angle of its shapes
            for fixture in body.fixtures:
                if body.userData['type']=='poly':
                    vertices=[(body.transform*v) for v in fixture.shape.vertices]
                    vertices=[w2a(v) for v in vertices]
                    body.userData['node'].pos=vertices
                elif body.userData['type']=='circle':
                    body.userData['node'].r=fixture.shape.radius*PPM
                    position=body.transform*fixture.shape.pos
                    body.userData['node'].pos=w2a(position)
                elif body.userData['type']=='line':
                    vertices=[body.transform*v for v in fixture.shape.vertices]
                    vertices = [w2a(v) for v in vertices]
                    body.userData['node'].pos1=vertices[0]
                    body.userData['node'].pos2=vertices[1]
        self.world.ClearForces()
        

      
class BatSpawner:
    def __init__(self,parentNode,world):
        self.world = world
        self.field = parentNode
        self.field.setEventHandler(avg.CURSORDOWN,avg.TOUCH,self.onDetect)
        #self.field.setEventHandler(avg.CURSORMOTION,avg.TOUCH,self.onMove)
        self.field.setEventHandler(avg.CURSORUP,avg.TOUCH,self.onUp)
        self.detected= False
        self.bat = None
        self.cid1=None
        self.cid2=None
        self.pos1=None
        self.pos2=None
    
    def onDetect(self,event):        
        if self.detected:
            self.cid2 =event.cursorid 
            self.field.setEventCapture(self.cid2)
            #self.pos2 = a2w(event.pos)
            self.pos2 = a2w(event.pos)
            self.bat = Bat(self.field, self.world, self.pos1, self.pos2)
        else:
            self.cid1 = event.cursorid
            self.field.setEventCapture(self.cid1)
            #self.pos1 = a2w(event.pos)
            self.pos1 = a2w(event.pos)
            self.detected = True

    def angle(self):
        vec = self.pos2 - self.pos1
        ang = math.atan2(vec.y, vec.x)
        if ang < 0:
            ang += math.pi * 2
        return ang
            
    def onMove(self,event):
        if event.cursorid == self.cid1 and self.bat is not None:
            self.pos1 = a2w(event.pos)           
            self.bat.update1(self.pos1)
        elif event.cursorid == self.cid2 and self.bat is not None:
            self.pos2 = a2w(event.pos)
            self.bat.update2(self.pos2)
    
    def onUp(self,event):
        self.field.releaseEventCapture(event.cursorid)
        self.detected = False
        if self.bat is not None:
            self.bat.destroy()
            self.bat=None