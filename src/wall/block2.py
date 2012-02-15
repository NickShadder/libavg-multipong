'''
Created on 15.02.2012

@author: Philipp
'''

from src.wall.block import Block
from src.wall.brick import Brick
from src.wall.constants import Constants

# this Block consists of two bricks
class Block2 (Block):
    
    def __init__(self, parentNode, x, y, colour):
        super(Block2, self).__init__(parentNode, colour)
        self.__brick0 = Brick(self.__parentNode, x, y, 0, colour)
        self.__brickList.append(self.__brick0)
        self.__brick1 = Brick(self.__parentNode, x, y - Constants.size[1], 1, colour)
        self.__brickList.append(self.__brick1)