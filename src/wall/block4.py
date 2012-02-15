'''
Created on 15.02.2012

@author: Philipp
'''

from src.wall import block
from src.wall import brick
from src.wall import constants

# this Block consists of four bricks which are arranged in a line
class Block4 (block.Block):
    
    def __init__(self, parentNode, x, y, colour):
        super(Block4, self).__init__(parentNode, colour)
        self.__brick0 = brick.Brick(self.__parentNode, x, y, 0, colour)
        self.__brickList.append(self.__brick0)
        self.__brick1 = brick.Brick(self.__parentNode, x, y - constants.size[1], 1, colour)
        self.__brickList.append(self.__brick1)
        self.__brick2 = brick.Brick(self.__parentNode, x, y - 2 * constants.size[1], 2, colour)
        self.__brickList.append(self.__brick2)
        self.__brick3 = brick.Brick(self.__parentNode, x, y + constants.size[1], 3, colour)
        self.__brickList.append(self.__brick3)