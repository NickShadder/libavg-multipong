'''
Created on 19.01.2012

@author: 2526240
'''

# ****************** general config ******************
debug = True
pointsToWin = 100
PPM = 20 # number of pixels per meter
#TARGET_FPS = 60 # the targeted frames per second
#TIME_STEP = 1.0 / TARGET_FPS # XXX rethink maybe .013 is better
TIME_STEP = .013

# ****************** bat config ******************
maxBatSize = 17 # maximal bat size in meters XXX should be dependent on the actual resolution

# ****************** wall config ******************
#size has to be an even number!!!
brickSize = 2 # the size of a brick in meter XXX should be dependent on the actual resolution / bricksPerLine
brickLines = 4
initialNumberOfBlocks = 10
maxNumOfRubberBricks = 9

# ****************** bonus config ******************
bonusTime = 3 # the time in seconds a bonus waits for interaction before disappearing
bonusMaximum = 10
# ****************** ball config ******************
maxBalls = 3 # the maximum number of pacmans on the field 
ballRadius = 1.2 # the radius of a pacman in meters

# ****************** ghost config ******************
ghostRadius = 1.8 # the radius of a ghost in meters
