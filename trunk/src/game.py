'''
Created on 19.01.2012

@author: 2526240
'''

from libavg import avg,gameapp,ui
from Box2D import b2World,b2EdgeShape,b2Vec2
from gameobjects import Bat,Ball

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
        # setup player fields
        fieldSize = (displayWidth/3,displayHeight)
        self.field1 = avg.DivNode(parent=self.display,size=fieldSize,elementoutlinecolor='00FF00')
        self.field2 = avg.DivNode(parent=self.display,size=fieldSize,elementoutlinecolor='0000FF',pos=(displayWidth*2/3,0))
        # setup bat handlers
        #self.bathandler1 = ui.TransformRecognizer(self.field1, self.display, eventSource=avg.TOUCH, moveHandler=self.found)
        
    # pybox2d setup
        # create world
        self.world=b2World(gravity=(0,10),doSleep=True)
                
        # create sides
        upperBound = avg.LineNode(parent=self.display,pos1=(0,1),pos2=(displayWidth,1))
        lowerBound = avg.LineNode(parent=self.display,pos1=(0,displayHeight-1),pos2=(displayWidth,displayHeight-1))
        d = {'type':'line','node':upperBound}
        self.world.CreateStaticBody(userData=d,position=a2w((0,1)),shapes=b2EdgeShape(vertices=[a2w((0,1)),a2w((displayWidth,1))]))
        d['node']=lowerBound
        self.world.CreateStaticBody(userData=d,position=a2w((0,1)),shapes=b2EdgeShape(vertices=[a2w((0,displayHeight-1)),a2w((displayWidth,displayHeight-1))]))
                
        # create balls
        self.balls=[Ball(self.display,self.world,(15,20),1)]
        
        # experimental bats
        bat = Bat(self.display,self.world,(10,35),(20,40))
        bat2 = Bat(self.display,self.world,(55,40),(60,45))
        
    # setup drawing of the world
        g_player.setInterval(16,self.renderjob) # TODO setOnFrameHanlder?
        

    def renderjob(self):
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
        self.world.Step(TIME_STEP, 10, 10)
        self.world.ClearForces()