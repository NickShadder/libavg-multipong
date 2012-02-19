'''
Created on 19.01.2012

@author: 2526240
'''

# ****************** general config ******************
debug = True
PPM = 20.0 # number of pixels per meter
TARGET_FPS = 60 # the targeted frames per second
TIME_STEP = 1.0 / TARGET_FPS

# ****************** bat config ******************
maxBatSize = 10 # maximal bat size in meters XXX should be dependent on the actual resolution

# ****************** wall config ******************
brickSize = (50, 50) # the size of a brick in pixels XXX should be dependent on the actual resolution
initialNumberOfBlocks = 10
maxNumberOfBlocks = 30

# ****************** bonus config ******************
bonusTime = 3 # the time in seconds a bonus waits for interaction before disappearing

# ****************** ball config ******************
maxBalls = 3 # the maximum number of pacmans on the field 
ballRadius = 1 # the radius of a pacman in meters

# ****************** ghost config ******************
ghostRadius = 2 # the radius of a ghost in meters