'''
Created on 15.02.2012

@author: Philipp
'''

from src.wall.block import Block
from src.wall.brick import Brick
from src.wall.constants import Constants

# this Block consists of four bricks which form an rectangle
class Block3 (Block):
    
    def __init__(self, parentNode, x, y, colour):
        super(Block3, self).__init__(parentNode, colour)
        self.__brick0 = Brick(self.__parentNode, x, y, 0, colour)
        self.__brickList.append(self.__brick0)
        self.__brick1 = Brick(self.__parentNode, x, y - Constants.size[1], 1, colour)
        self.__brickList.append(self.__brick1)
        # if the block should appear on the left side:
        if self.__position == 1:
            self.__brick2 = Brick(self.__parentNode, x + Constants.size[0], y, 2, colour)
            self.__brickList.append(self.__brick2)
            self.__brick3 = Brick(self.__parentNode, x + Constants.size[0], y - Constants.size[1], 3, colour)
            self.__brickList.append(self.__brick3)
        # if the block should appear on the right side:
        if self.__position == 0:
            self.__brick2 = Brick(self.__parentNode, x - Constants.size[0], y, 2, colour)
            self.__brickList.append(self.__brick2)
            self.__brick3 = Brick(self.__parentNode, x - Constants.size[0], y - Constants.size[1], 3, colour)
            self.__brickList.append(self.__brick3)