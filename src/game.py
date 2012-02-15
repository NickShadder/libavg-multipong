'''
Created on 19.01.2012

@author: 2526240
'''

from display import Display
from libavg import avg,gameapp
from Box2D import b2World, b2PolygonShape

g_player = avg.Player.get() # globally store the avg player
PPM=20.0 # pixels per meter
TARGET_FPS=60
TIME_STEP=1.0/TARGET_FPS

class Game(gameapp.GameApp):
    def init(self):
        # libavg setup
        self.display = Display(self._parentNode)
        
        # pybox2d setup
        self.world=b2World(gravity=(0,-5),doSleep=True)
        
        # create floor
        node=avg.PolygonNode(parent=self.display)
        d = {'type':'poly','node':node}
        self.world.CreateStaticBody(userData=d,position=(0,1),shapes=b2PolygonShape(box=(50,5)))
        
        # create a rect
        node=avg.PolygonNode(parent=self.display)
        d = {'type':'poly','node':node}
        rect=self.world.CreateDynamicBody(position=(10,30), angle=10,userData=d)
        rect.CreatePolygonFixture(box=(2,1), density=1, friction=0.3,restitution=.3)
        
        # create a circle
        node=avg.CircleNode(parent=self.display,fillopacity=1, fillcolor="FF1337")
        d={'type':'circle','node':node}
        circle = self.world.CreateDynamicBody(position=(15,20),userData=d)
        circle.CreateCircleFixture(radius=0.5, density=1, friction=0.3,restitution=.73)
        
        # setup drawing of the world
        g_player.setInterval(16,self.renderjob)
        

    def renderjob(self):
        for body in self.world.bodies:  # inefficient
            # The body gives us the position and angle of its shapes
            for fixture in body.fixtures:
                if body.userData['type']=='poly':
                    vertices=[(body.transform*v)*PPM for v in fixture.shape.vertices]
                    vertices=[(v[0], self._parentNode.height-v[1]) for v in vertices] # reverse y axis
                    body.userData['node'].pos=vertices
                elif body.userData['type']=='circle':
                    body.userData['node'].r=fixture.shape.radius*PPM
                    position=body.transform*fixture.shape.pos*PPM
                    position=(position[0],self._parentNode.height-position[1]) # reverse y axis
                    body.userData['node'].pos=position
        self.world.Step(TIME_STEP, 10, 10)
        self.world.ClearForces()