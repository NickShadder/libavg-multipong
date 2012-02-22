'''
Created on 15.02.2012

@author: Philipp
'''

from config import brickSize
from brick import Brick

halfBrickSize = brickSize / 2

# appears as building material - consists of bricks - !Superclass! there are several types of Blocks
# position: indicates on which side the block should appear (left or right) - important to compute the coordinates - 1: left, 0: right
# brickList contains the bricks which were not hit so far
class Block (object):
    
    def __init__(self, parentNode, colour):
        self.parentNode = parentNode
        self.colour = colour
        self.brickList = []
    

# this Block consists only of one brick
class SingleBlock (Block):    
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(self, parentNode, colour)
        self.brick0 = Brick(self.parentNode, x - halfBrickSize, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
    
    def move(self, offset, event, number):
        self.brick0.pos = (event.x - offset[0], event.y - offset[1])
        
        
# this Block consists of two bricks
class DoubleBlock (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(self, parentNode, colour)
        self.brick0 = Brick(self.parentNode, x - halfBrickSize, y - brickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x - halfBrickSize, y, colour, self)
        self.brickList.append(self.brick1)
    
    def move(self, offset, event, number):
        pos = (event.x - offset[0], event.y - offset[1])
        if number == 0:
            self.brick0.pos = pos
            self.brick1.pos = (pos[0], pos[1] - brickSize[1])
        elif number == 1:
            self.brick1.pos = pos
            self.brick0.pos = (pos[0], pos[1] + brickSize[1])
        

# this Block consists of four bricks which form an rectangle
class RectBlock (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(self, parentNode, colour)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - brickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - brickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x - brickSize, y, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x, y, colour, self)
        self.brickList.append(self.brick3)
        
    def move(self, offset, event, number):
        pos = (event.x - offset[0], event.y - offset[1])
        if number == 1:
            pos = (pos[0], pos[1] + brickSize[1])
        elif self.position == 1:
            if number == 2:
                pos = (pos[0] - brickSize[0], pos[1])
            elif number == 3:
                pos = (pos[0] - brickSize[0], pos[1] + brickSize[1])
        elif self.position == 0:
            if number == 2:
                pos = (pos[0] - brickSize[0], pos[1])
            elif number == 3:
                pos = (pos[0] - brickSize[0], pos[1] + brickSize[1])
        self.brick0.pos = pos
        self.brick1.pos = (pos[0], pos[1] - brickSize[1])
        if self.position == 1:
            self.brick2.pos = (pos[0] + brickSize[0], pos[1])
            self.brick3.pos = (pos[0] + brickSize[0], pos[1] - brickSize[1])
        elif self.position == 2:
            self.brick2.pos = (pos[0] - brickSize[0], pos[1])
            self.brick0.pos = (pos[0] - brickSize[0], pos[1] - brickSize[1])
            
# this Block consists of four bricks which are arranged in a line
class LineBlock (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(self, parentNode, colour)
        self.brick0 = Brick(self.parentNode, x - halfBrickSize, y - 2 * brickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x - halfBrickSize, y - brickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x - halfBrickSize, y, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x - halfBrickSize, y + brickSize, colour, self)
        self.brickList.append(self.brick3)
        
    def move(self, offset, event, number):
        pos = (event.x - offset[0], event.y - offset[1])
        if number == 1:
            pos = (pos[0], pos[1] + brickSize[1])
        elif number == 2:
            pos = (pos[0], pos[1] + 2 * brickSize[1])
        elif number == 3:
            pos = (pos[0], pos[1] - brickSize[1])
        self.brick0.pos = pos
        self.brick1.pos = (pos[0], pos[1] - brickSize[1])
        self.brick2.pos = (pos[0], pos[1] - 2 * brickSize[1])
        self.brick3.pos = (pos[0], pos[1] + brickSize[1])
        
        
#this Block consists of four bricks which are arranged like a L (left)
class LBlockLeft (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(self, parentNode, colour)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x  - brickSize, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick3)
    
    def move(self, offset, event, number):
        pos = (event.x - offset[0], event.y - offset[1])
        if number == 0:
            pos = (pos[0], pos[1] + brickSize[1] / 2)
        if number == 1:
            pos = (pos[0], pos[1] + 3 * brickSize[1] / 2)
        elif number == 2:
            pos = (pos[0], pos[1] + brickSize[1] / 2)
        elif self.position == 1:
            if number == 3:
                pos = (pos[0] - brickSize[0], pos[1] - brickSize[1] / 2)
        elif self.position == 0:
            if number == 3:
                pos = (pos[0] + brickSize[0], pos[1] - brickSize[1] / 2)
        self.brick0.pos = pos
        self.brick1.pos = (pos[0], pos[1] - 3 * brickSize[1] / 2)
        self.brick2.pos = (pos[0], pos[1] + brickSize[1] / 2)
        if self.position == 1:
            self.brick3.pos = (pos[0] + brickSize[0], pos[1] + brickSize[1] / 2)
        elif self.position == 0:
            self.brick3.pos = (pos[0] - brickSize[0], pos[1] + brickSize[1] / 2)


#this Block consists of four bricks which are arranged like a L (right - mirror inverted)
class LBlockRight (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(self, parentNode, colour)
        self.brick0 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick3)


#this Block consists of four bricks which are arranged like an uppercase gamma (left)
class GammaBlockLeft (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(self, parentNode, colour)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x  - brickSize, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick3)


#this Block consists of four bricks which are arranged like an uppercase gamma (right - mirror inverted)
class GammaBlockRight (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(self, parentNode, colour)
        self.brick0 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick3)


# this Block consists of three bricks which are arranged in a line, in the middle a fourth brick is added (left)
class MiddleBlockLeft (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(self, parentNode, colour)
        self.brick0 = Brick(self.parentNode, x - brickSize, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x  - brickSize, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x - brickSize, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick3)


# this Block consists of three bricks which are arranged in a line, in the middle a fourth brick is added (right - mirror inverted)
class MiddleBlockRight (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(self, parentNode, colour)
        self.brick0 = Brick(self.parentNode, x, y - 3 * halfBrickSize, colour, self)
        self.brickList.append(self.brick0)
        self.brick1 = Brick(self.parentNode, x, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick1)
        self.brick2 = Brick(self.parentNode, x, y + halfBrickSize, colour, self)
        self.brickList.append(self.brick2)
        self.brick3 = Brick(self.parentNode, x - brickSize, y - halfBrickSize, colour, self)
        self.brickList.append(self.brick3)