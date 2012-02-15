'''
Created on 15.02.2012

@author: Philipp
'''

from libavg import AVGApp, avg
from block import SingleBlock


#    liste mit nicht vanished bricks, wenn leer -> ruft methode in oberklasse auf, objekt wird neu eingereiht
#       randX = random.randint(0,1000)
#          for i in range (20):


class Wall (AVGApp):


    def __init__(self, parentNode):
        
        self.__divNode = avg.DivNode (size = parentNode.size, parent = parentNode)
                
        #self.__Rect.setEventHandler (avg.CURSORDOWN, avg.TOUCH, self.__startPinch)
        #self.__Rect.setEventHandler (avg.CURSORMOTION, avg.TOUCH, self.__doPinch)
        #self.__divNode.setEventHandler (avg.CURSORUP, avg.TOUCH, self.__endPinch)
        
        self.__testCursor = True
        
        self.__cursor1 = None
        self.__cursor2 = None
        self.__pos1x = None
        self.__pos1y = None
        self.__pos2x = None
        self.__pos2y = None
        self.__x = None
        self.__y = None
    
    
    def __nextBlock(self):
        b = SingleBlock(self.__divNode, 20, 20, "00FF00")
        
    def __startPinch (self, event):
        if self.__testCursor:
            if self.__cursor1 == None:
                self.__cursor1 = event.cursorid
                self.__pos1x = event.pos.x
                self.__pos1y = event.pos.y
            elif (self.__cursor2 == None) & (event.cursorid <> self.__cursor1):
                self.__cursor2 = event.cursorid
                self.__pos2x = event.pos.x
                self.__pos2y = event.pos.y
                self.__testCursor = False
    
    
    def __doPinch (self, event):
        if not self.__testCursor:
            if event.cursorid == self.__cursor1:
                if self.__pos1x > self.__pos2x:
                    self.__x = event.pos.x - self.__pos1x
                else:
                    self.__x = self.__pos1x - event.pos.x
                if self.__pos1y > self.__pos2y:
                    self.__y = event.pos.y - self.__pos1y
                else:
                    self.__y = self.__pos1y - event.pos.y
                m = max (self.__x, self.__y)
                event.node.size = (event.node.size.x + m, event.node.size.y + m)
                event.node.pos = (event.node.pos.x - m / 2, event.node.pos.y - m / 2)
                self.__pos1x = event.pos.x
                self.__pos1y = event.pos.y
            if event.cursorid == self.__cursor2:
                if self.__pos2x > self.__pos1x:
                    self.__x = event.pos.x - self.__pos2x
                else:
                    self.__x = self.__pos2x - event.pos.x
                if self.__pos2y > self.__pos1y:
                    self.__y = event.pos.y - self.__pos2y
                else:
                    self.__y = self.__pos2y - event.pos.y
                m = max (self.__x, self.__y)
                event.node.size = (event.node.size.x + m, event.node.size.y + m)
                event.node.pos = (event.node.pos.x - m / 2, event.node.pos.y - m / 2)
                self.__pos2x = event.pos.x
                self.__pos2y = event.pos.y
    
    
    def __endPinch (self, event):
        if not self.__testCursor:
            self.__testCursor = True
            self.__cursor1 = None
            self.__cursor2 = None


if __name__ == '__main__':
    Wall.start (resolution = (1024, 768))