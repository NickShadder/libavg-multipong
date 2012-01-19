'''
Created on 18.01.2012

@author: 2526240
'''

from engine.game import Game
from logic import config


if __name__ == '__main__':
    if config.debug: 
        print "DEBUG: Starting Application: ",config.resX,"x",config.resY
    Game.start(resolution=(config.resX, config.resY))
    if config.debug:
        print "DEBUG: Leaving main" 
    