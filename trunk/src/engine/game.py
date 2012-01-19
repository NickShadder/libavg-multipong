'''
Created on 19.01.2012

@author: 2526240
'''
from libavg import avg,AVGApp
from logic import config
from engine.display import Display

g_player = avg.Player.get() # globally store the avg player

class Game(AVGApp):
    def __init__(self,parentNode):
        # g_player.enableMultitouch() # should be uncommented in the final version
        self.display = Display((config.resX, config.resY), parentNode) 
        #TODO create logic here
        pass