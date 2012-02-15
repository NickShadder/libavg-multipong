'''
Created on 15.02.2012

@author: Philipp
'''

import config
from brick import Brick

# appears as building material - consists of bricks - !Superclass! there are several types of Blocks
# position: indicates on which side the block should appear (left or right) - important to compute the coordinates - 1: left, 0: right
# brickList contains the bricks which were not hit so far
class Block (object):
    
    
    def __init__(self, parentNode, colour, position):
        self.parentNode = parentNode
        self.colour = colour
        self.position = position
        self.brickList = []
    
    def __change_position(self, xDif, yDif):
        for brick in self.brickList:
            brick.pos = (brick.pos[0] + xDif, brick.pos[1] + yDif)
    
    def move(self, pos, event):
        self.__change_position(event.x - pos[0], event.y - pos[1])



# this Block consists only of one brick
class SingleBlock (Block):    
    def __init__(self, parentNode, x, y, colour, position):
        Block.__init__(self, parentNode, colour, position)
        self.brick0 = Brick(self.parentNode, x, y, 0, colour, self)
        self.brickList.append(self.brick0)
        
        
# this Block consists of two bricks
class TwoBlock (Block):
    def __init__(self, parentNode, x, y, colour, position):
        Block.__init__(self, parentNode, colour, position)
        self.brick0 = Brick(self.parentNode, x, y, 0, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - config.brickSize[1], 1, colour, self)
        self.brickList.append(self.brick1)
        

# this Block consists of four bricks which form an rectangle
class RectBlock (Block):
    def __init__(self, parentNode, x, y, colour, position):
        Block.__init__(self, parentNode, colour, position)
        self.brick0 = Brick(self.parentNode, x, y, 0, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - config.brickSize[1], 1, colour, self)
        self.brickList.append(self.brick1)
        # if the block should appear on the left side:
        if self.position == 1:
            self.brick2 = Brick(self.parentNode, x + config.brickSize[0], y, 2, colour, self)
            self.brickList.append(self.brick2)
            self.brick3 = Brick(self.parentNode, x + config.brickSize[0], y - config.brickSize[1], 3, colour, self)
            self.brickList.append(self.brick3)
        # if the block should appear on the right side:
        if self.position == 0:
            self.brick2 = Brick(self.parentNode, x - config.brickSize[0], y, 2, colour, self)
            self.brickList.append(self.brick2)
            self.brick3 = Brick(self.parentNode, x - config.brickSize[0], y - config.brickSize[1], 3, colour, self)
            self.brickList.append(self.brick3)
            
# this Block consists of four bricks which are arranged in a line
class LineBlock (Block):
    def __init__(self, parentNode, x, y, colour, position):
        Block.__init__(self, parentNode, colour, position)
        self.brick0 = Brick(self.parentNode, x, y, 0, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - config.brickSize[1], 1, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x, y - 2 * config.brickSize[1], 2, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x, y + config.brickSize[1], 3, colour, self)
        self.brickList.append(self.brick3)
        
        
#this Block consists of four bricks which are arranged like a L
class LBlock (Block):
    def __init__(self, parentNode, x, y, colour, position):
        Block.__init__(self, parentNode, colour, position)
        self.brick0 = Brick(self.parentNode, x, y - config.brickSize[1] / 2, 0, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - 3 * config.brickSize[1] / 2, 1, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x, y + config.brickSize[1] / 2, 2, colour, self)
        self.brickList.append(self.brick2)
        # if the block should appear on the left side:
        if self.position == 1:
            self.brick3 = Brick(self.parentNode, x + config.brickSize[0], y + config.brickSize[1] / 2, 3, colour, self)
            self.brickList.append(self.brick3)
        # if the block should appear on the right side:
        if self.position == 0:
            self.brick3 = Brick(self.parentNode, x - config.brickSize[0], y + config.brickSize[1] / 2, 3, colour, self)
            self.brickList.append(self.brick3)        