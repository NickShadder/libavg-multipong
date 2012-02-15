'''
Created on 15.02.2012

@author: 2528449
'''

from libavg import avg
from Box2D import b2World, b2PolygonShape

# creates a ball with the given x,y coordinates and radius
class Ball(object):

   def __init__(self, parentNode, world, x, y, radius):
       self.parent = parentNode
       self.radius = radius
       self.world = world
       self.node=avg.CircleNode(parent=self.parent,fillopacity=1, fillcolor="FFFF00")
       self.d={'type':'circle','node':self.node}
       self.circle = self.world.CreateDynamicBody(position=(x,y),userData=self.d)
       self.circle.CreateCircleFixture(radius=self.radius, density=0, friction=0.3,restitution=1)
