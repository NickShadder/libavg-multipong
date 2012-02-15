'''
Created on 15.02.2012

@author: Philipp
'''

from src.wall.block import Block
from src.wall.brick import Brick

# this Block consists only of one brick
class Block1 (Block):
    
    def __init__(self, parentNode, x, y, colour):
        super(Block1, self).__init__(parentNode, colour)
        self.__brick0 = Brick(self.__parentNode, x, y, 0, colour)
        self.__brickList.append(self.__brick0)