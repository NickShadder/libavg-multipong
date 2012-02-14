'''
Created on 19.01.2012

@author: 2526240
'''
from libavg import avg,gameapp
from engine.display import Display
from Box2D import b2World, b2PolygonShape

g_player = avg.Player.get() # globally store the avg player
PPM=20.0 # pixels per meter
TARGET_FPS=60
TIME_STEP=1.0/TARGET_FPS


class Game(gameapp.GameApp):
    def init(self):
        # libavg setup
        self.display = Display(self._parentNode)
        
        self.n1 = avg.PolygonNode(parent=self.display)
        self.n2 = avg.PolygonNode(parent=self.display)
        
        # pybox2d setup
        self.world=b2World(gravity=(0,-5),doSleep=True)
        self.ground_body=self.world.CreateStaticBody(position=(0,1),density=1,shapes=b2PolygonShape(box=(50,5)),)
        self.rect=self.world.CreateDynamicBody(position=(10,15), angle=15)
        self.rect.CreatePolygonFixture(box=(2,1), density=1, friction=0.3)
        #self.circle = self.world.CreateDynamicBody(position=(12,5))
        #self.circle.CreateCircleFixture(radius=0.5, density=1, friction=0.3)
        
        
        g_player.setOnFrameHandler(self.renderjob)
        
        
    def _enter(self):
        pass
    
    def _leave(self):
        pass
    
    def renderjob(self):
        for body in self.world.bodies:
            # The body gives us the position and angle of its shapes
            for fixture in body.fixtures:
                # The fixture holds information like density and friction,
                # and also the shape.
                shape=fixture.shape
                
                # Naively assume that this is a polygon shape. (not good normally!)
                # We take the body's transform and multiply it with each 
                # vertex, and then convert from meters to pixels with the scale
                # factor. 
                vertices=[(body.transform*v)*PPM for v in shape.vertices]
    
                # But wait! It's upside-down! Pygame and Box2D orient their
                # axes in different ways. Box2D is just like how you learned
                # in high school, with positive x and y directions going
                # right and up. Pygame, on the other hand, increases in the
                # right and downward directions. This means we must flip
                # the y components.
                vertices=[(v[0], 1024-v[1]) for v in vertices]
                if body==self.rect:
                    self.n1.pos=vertices
                else:
                    self.n2.pos=vertices
    
            # Make Box2D simulate the physics of our world for one step.
            # Instruct the world to perform a single step of simulation. It is
            # generally best to keep the time step and iterations fixed.
            # See the manual (Section "Simulating the World") for further discussion
            # on these parameters and their implications.
            self.world.Step(TIME_STEP, 10, 10)