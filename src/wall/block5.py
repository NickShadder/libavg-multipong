'''
Created on 15.02.2012

@author: Philipp
'''

from src.wall.block import Block
from src.wall.brick import Brick
from src.wall.constants import Constants

#this Block consists of four bricks which are arranged like a L
class Block5 (Block):
    
    def __init__(self, parentNode, x, y, colour):
        super(Block5, self).__init__(parentNode, colour)
        self.__brick0 = Brick(self.__parentNode, x, y - Constants.size[1] / 2, 0, colour)
        self.__brickList.append(self.__brick0)
        self.__brick1 = Brick(self.__parentNode, x, y - 3 * Constants.size[1] / 2, 1, colour)
        self.__brickList.append(self.__brick1)
        self.__brick2 = Brick(self.__parentNode, x, y + Constants.size[1] / 2, 2, colour)
        self.__brickList.append(self.__brick2)
        # if the block should appear on the left side:
        if self.__position == 1:
            self.__brick3 = Brick(self.__parentNode, x + Constants.size[0], y - Constants.size[1] / 2, 3, colour)
            self.__brickList.append(self.__brick3)
        # if the block should appear on the right side:
        if self.__position == 0:
            self.__brick3 = Brick(self.__parentNode, x - Constants.size[0], y - Constants.size[1] / 2, 3, colour)
            self.__brickList.append(self.__brick3)