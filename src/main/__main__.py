'''
Created on 18.01.2012

@author: 2526240
'''

from engine.game import Game
from logic import config

if __name__ == '__main__':
    if config.debug: 
        print "DEBUG: Starting Application"
    Game.start()
    if config.debug:
        print "DEBUG: Leaving main" 
    