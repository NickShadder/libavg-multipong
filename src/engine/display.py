'''
Created on 19.01.2012

@author: 2526240
'''
from libavg import avg
from logic import config

class Display(avg.DivNode):
    def __init__(self, size, parent):
        avg.DivNode.__init__(self, size=size, parent=parent)
        # TODO
        # there should be one background for the main menu
        # and multiple backgrounds reflecting current level
        # (space, underwater, sand, asphalt etc.)
        self.background = avg.ImageNode(pos = (0,0), 
                    size = (config.resX, config.resY),                    
                    href = '../../data/img/silly.png',parent=self,) # a silly temporary background
        