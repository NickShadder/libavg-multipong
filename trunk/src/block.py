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
        self.__parentNode = parentNode
        self.__colour = colour
        self.__position = position
        self.__brickList = []
        
# this Block consists only of one brick
class SingleBlock (Block):    
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(parentNode, colour)
        self.__brick0 = Brick(self.__parentNode, x, y, 0, colour)
        self.__brickList.append(self.__brick0)
        
        
# this Block consists of two bricks
class TwoBlock (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(parentNode, colour)
        self.__brick0 = Brick(self.__parentNode, x, y, 0, colour)
        self.__brickList.append(self.__brick0)
        self.__brick1 = Brick(self.__parentNode, x, y - config.brickSize[1], 1, colour)
        self.__brickList.append(self.__brick1)
        

# this Block consists of four bricks which form an rectangle
class RectBlock (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(parentNode, colour)
        self.__brick0 = Brick(self.__parentNode, x, y, 0, colour)
        self.__brickList.append(self.__brick0)
        self.__brick1 = Brick(self.__parentNode, x, y - config.brickSize[1], 1, colour)
        self.__brickList.append(self.__brick1)
        # if the block should appear on the left side:
        if self.__position == 1:
            self.__brick2 = Brick(self.__parentNode, x + config.brickSize[0], y, 2, colour)
            self.__brickList.append(self.__brick2)
            self.__brick3 = Brick(self.__parentNode, x + config.brickSize[0], y - config.brickSize[1], 3, colour)
            self.__brickList.append(self.__brick3)
        # if the block should appear on the right side:
        if self.__position == 0:
            self.__brick2 = Brick(self.__parentNode, x - config.brickSize[0], y, 2, colour)
            self.__brickList.append(self.__brick2)
            self.__brick3 = Brick(self.__parentNode, x - config.brickSize[0], y - config.brickSize[1], 3, colour)
            self.__brickList.append(self.__brick3)
            
# this Block consists of four bricks which are arranged in a line
class LineBlock (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(parentNode, colour)
        self.__brick0 = Brick(self.__parentNode, x, y, 0, colour)
        self.__brickList.append(self.__brick0)
        self.__brick1 = Brick(self.__parentNode, x, y - config.brickSize[1], 1, colour)
        self.__brickList.append(self.__brick1)
        self.__brick2 = Brick(self.__parentNode, x, y - 2 * config.brickSize[1], 2, colour)
        self.__brickList.append(self.__brick2)
        self.__brick3 = Brick(self.__parentNode, x, y + config.brickSize[1], 3, colour)
        self.__brickList.append(self.__brick3)
        
        
#this Block consists of four bricks which are arranged like a L
class LBrick (Block):
    def __init__(self, parentNode, x, y, colour):
        Block.__init__(parentNode, colour)
        self.__brick0 = Brick(self.__parentNode, x, y - config.brickSize[1] / 2, 0, colour)
        self.__brickList.append(self.__brick0)
        self.__brick1 = Brick(self.__parentNode, x, y - 3 * config.brickSize[1] / 2, 1, colour)
        self.__brickList.append(self.__brick1)
        self.__brick2 = Brick(self.__parentNode, x, y + config.brickSize[1] / 2, 2, colour)
        self.__brickList.append(self.__brick2)
        # if the block should appear on the left side:
        if self.__position == 1:
            self.__brick3 = Brick(self.__parentNode, x + config.brickSize[0], y - config.brickSize[1] / 2, 3, colour)
            self.__brickList.append(self.__brick3)
        # if the block should appear on the right side:
        if self.__position == 0:
            self.__brick3 = Brick(self.__parentNode, x - config.brickSize[0], y - config.brickSize[1] / 2, 3, colour)
            self.__brickList.append(self.__brick3)        