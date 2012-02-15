'''
Created on 15.02.2012

@author: Philipp
'''

from src.wall import block
from src.wall import brick

# this Block consists only of one brick
class Block1 (block.Block):
    
    def __init__(self, parentNode, x, y, colour):
        super(Block1, self).__init__(parentNode, colour)
        self.__brick0 = brick.Brick(self.__parentNode, x, y, 0, colour)
        self.__brickList.append(self.__brick0)