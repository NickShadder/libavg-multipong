'''
Created on 15.02.2012

@author: Philipp
'''

# appears as building material - consists of bricks - !Superclass! there are several types of Blocks
# position: indicates on which side the block should appear (left or right) - important to compute the coordinates - 1: left, 0: right
# brickList contains the bricks which were not hit so far
class Block (object):
    
    def __init__(self, parentNode, colour, position):
        self.__parentNode = parentNode
        self.__colour = colour
        self.__position = position
        self.__brickList = []