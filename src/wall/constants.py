'''
Created on 15.02.2012

@author: Philipp
'''

# distance to the margin for the right player must be chosen +'size' wider

class Constants (object):
    # the size of a brick (piece of a block)
    size = (20, 20)

    # the time the player have to drag the block before the next appears
    period = 0.3

    # the position where the blocks appear
    leftPosition = (30, 30)
    rightPosition = (30, 60)

    # the number of Blocks for each player at the beginning and maximum
    initialNumberOfBlocks = 10
    maxNumberOfBlocks = 15