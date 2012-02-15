'''
Created on 15.02.2012

@author: Philipp
'''

from libavg import avg
from src.wall.constants import Constants

# a piece of a block
# x, y - coordinates
# number - counts of how many bricks the respective block consists; number = 1, if this brick is the first element in the list in Block
class Brick (avg.RectNode):
    
    def __init__(self, parentNode, x, y, number, colour):
        super(Brick, self).__init__(Constants.size, pos= (x, y), fillopacity = 1, fillcolor = colour, parent = parentNode)
        self.__number = number
        
    # is called, when the ball hits the brick
    def vanish(self):
        self.fillopacity = 0