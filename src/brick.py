'''
Created on 15.02.2012

@author: Philipp
'''

import config
from libavg import avg

# a piece of a block
# x, y - coordinates
# number - counts of how many bricks the respective block consists; number = 1, if this brick is the first element in the list in Block
class Brick (avg.RectNode):
    
    def __init__(self, parentNode, x, y, number, colour, parentBlock):
        super(Brick, self).__init__(size = config.brickSize, pos= (x, y), fillopacity = 1, fillcolor = colour, parent = parentNode)
        self.number = number
        self.__parentBlock = parentBlock
        self.setEventHandler (avg.CURSORDOWN, avg.TOUCH, self.__touch)
        self.setEventHandler (avg.CURSORMOTION, avg.TOUCH, self.__move)
    
    def __touch(self, event):
        self.__currentCursor = event.cursorid
        self.__currentPosition = self.getRelPos((event.x, event.y))
    
    def __move(self, event):
        if event.cursorid == self.__currentCursor:
            self.__parentBlock.move(self.__currentPosition, event)
        
    # is called, when the ball hits the brick
    def vanish(self):
        self.fillopacity = 0
        # todo there should be more than this here