'''
Created on 19.01.2012

@author: 2526240
'''

debug = True

maxBatSize = 15 # maximal bat size in meters

brickSize = (50, 50) # the size of a brick (piece of a block)

period = 0.3 # the time the player have to drag the block before the next appears

# the position where the blocks appear
leftPosition = (100, 100)
rightPosition = (500, 100)

# the number of Blocks for each player at the beginning and maximum
initialNumberOfBlocks = 10
maxNumberOfBlocks = 15

PPM = 20.0 # number of pixels per meter
TARGET_FPS = 60 # the targeted frames per second
TIME_STEP = 1.0 / TARGET_FPS