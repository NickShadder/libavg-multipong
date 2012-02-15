'''
Created on 15.02.2012

@author: Philipp
'''

from src.wall import block
from src.wall import brick
from src.wall import constants

#this Block consists of four bricks which are arranged like a L
class Block5 (block.Block):
    
    def __init__(self, parentNode, x, y, colour):
        super(Block5, self).__init__(parentNode, colour)
        self.__brick0 = brick.Brick(self.__parentNode, x, y - constants.size[1] / 2, 0, colour)
        self.__brickList.append(self.__brick0)
        self.__brick1 = brick.Brick(self.__parentNode, x, y - 3 * constants.size[1] / 2, 1, colour)
        self.__brickList.append(self.__brick1)
        self.__brick2 = brick.Brick(self.__parentNode, x, y + constants.size[1] / 2, 2, colour)
        self.__brickList.append(self.__brick2)
        # if the block should appear on the left side:
        if self.__position == 1:
            self.__brick3 = brick.Brick(self.__parentNode, x + constants.size[0], y - constants.size[1] / 2, 3, colour)
            self.__brickList.append(self.__brick3)
        # if the block should appear on the right side:
        if self.__position == 0:
            self.__brick3 = brick.Brick(self.__parentNode, x - constants.size[0], y - constants.size[1] / 2, 3, colour)
            self.__brickList.append(self.__brick3)