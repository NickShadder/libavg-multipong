'''
Created on 19.01.2012

@author: 2526240
'''
from libavg import avg

class Display(avg.DivNode):
    def __init__(self, myparent):
        avg.DivNode.__init__(self,parent=myparent,size=myparent.size,elementoutlinecolor="00FF00")
        avg.WordsNode(text="This is a test sentence.",pos=(50,50),parent=self)