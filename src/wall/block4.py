'''
Created on 15.02.2012

@author: Philipp
'''

from src.wall.block import Block
from src.wall.brick import Brick
from src.wall.constants import Constants

# this Block consists of four bricks which are arranged in a line
class Block4 (Block):
    
    def __init__(self, parentNode, x, y, colour):
        super(Block4, self).__init__(parentNode, colour)
        self.__brick0 = Brick(self.__parentNode, x, y, 0, colour)
        self.__brickList.append(self.__brick0)
        self.__brick1 = Brick(self.__parentNode, x, y - Constants.size[1], 1, colour)
        self.__brickList.append(self.__brick1)
        self.__brick2 = Brick(self.__parentNode, x, y - 2 * Constants.size[1], 2, colour)
        self.__brickList.append(self.__brick2)
        self.__brick3 = Brick(self.__parentNode, x, y + Constants.size[1], 3, colour)
        self.__brickList.append(self.__brick3)