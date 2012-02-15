'''
Created on 15.02.2012

@author: Philipp
'''

from libavg import AVGApp, avg
from copy import copy
import time, threading, random

from src.wall import constants, block1, block2, block3, block4, block5


#    liste mit nicht vanished bricks, wenn leer -> ruft methode in oberklasse auf, objekt wird neu eingereiht
 #   randX = random.randint(0,1000)
  #      for i in range (20):


class Wall (AVGApp):


    def __init__(self, parentNode):
        
        self.__divNode = avg.DivNode (size = parentNode.size, parent = parentNode)
        
        timer = threading.Timer(constants.period, self.__nextBlock)
        timer.start()
        
        self.__Rect.setEventHandler (avg.CURSORDOWN, avg.TOUCH, self.__startPinch)
        self.__Rect.setEventHandler (avg.CURSORMOTION, avg.TOUCH, self.__doPinch)
        self.__divNode.setEventHandler (avg.CURSORUP, avg.TOUCH, self.__endPinch)
        
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
        i = None
        
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


player = avg.Player.get()
player.loadFile ("text.avg")


#hole alle rec-nodes
untenlinksrot = player.getElementByID ("untenlinksrot")
obenlinksgruen = player.getElementByID ("obenlinksgruen")
mitteblau = player.getElementByID ("mitteblau")
untenrechtsgelb = player.getElementByID ("untenrechtsgelb")
maindiv = player.getElementByID ("maindiv")
#speichere Breite und Hoehe des div-node in x und y
x = maindiv.width 
y = maindiv.height
#passe entsprechend Koordinaten der linken oberen Ecken der Rechtecke an
untenlinksrot.pos = (0, y - 200)
#sichere fuer spaeter Koordinaten fuer blaues mittleres Rechteck
mx = x / 2 - 50
my = y / 2 - 50
#weise Koordinaten zu
mitteblau.pos = (mx, my)
#Rand des gelben Rechtecks verschwinden lassen
untenrechtsgelb.strokewidth = 0
untenrechtsgelb.pos = (x - 50, y - 50)


#Wert zeigt an, ob gelbes Rechteck gerade angezeigt wird
showURG = False
offset = None

def onMouseDownBlue(event):
    global offset
    node = event.node
    #aktuelle Koordinaten der linken oberen Ecke des blauen Rechtecks
    (a, b) = node.pos
    #Koordinaten des Mauszeigers abzueglich der eben ermittelten des Rechtecks
    offset = node.getRelPos((event.x - a, event.y - b))
    node.setEventCapture()
    #lasse gruenes Rechteck waehrend des Vorgangs verschwinden
    obenlinksgruen.fillopacity = 0
    obenlinksgruen.strokewidth = 0

#bei Klick auf das gruene Rechteck werden die Koordinaten des blauen
#wieder auf Ausgangswerte zurueckgesetzt (s.o.)
def onMouseDownGreen(event):
    global showURG
    mitteblau.pos = (mx, my)
    #da nun das rote Rechteck nicht mehr ueberdeckt sein kann,
    #pruefen, ob gelbes Rechteck noch angezeigt wird
    if showURG == True:
        #falls ja, opacity auf 0 setzen und das Verschwinden in showURG speichern
        showURG = False
        untenrechtsgelb.fillopacity = 0
        untenrechtsgelb.strokewidth = 0

def onMouseMoveBlue(event):
    global offset
    global showURG
    node = event.node
    #nur, wenn zuvor auf das Rechteck geklickt wurde und ein Wert in offset abgelegt wurde
    if offset != None:
        #neue Koordinaten ergeben sich aus aktueller Position des Mauszeiger
        #abzueglich eben ermittelter Differenz
        node.pos = (event.x - offset[0], event.y - offset[1])
        #neue Koordinaten in c und d speichern und pruefen, ob rotes Rechteck ueberdeckt
        (c, d) = node.pos
        if (c < 201) and (d > y - 300):
            #nur, falls gelbes Rechteck nicht bereits angezeigt wird
            if showURG == False:
                #damit der Wert fuer opacity nicht wiederholt gespeichert wird - showURG auf True setzen
                showURG = True
                untenrechtsgelb.fillopacity = 1
                untenrechtsgelb.strokewidth = 1
        else:
            #wird das rote Rechteck nicht ueberdeckt, pruefen, ob gelbes Rechteck noch angezeigt wird
            if showURG == True:
                #s.o.
                showURG = False
                untenrechtsgelb.fillopacity = 0
                untenrechtsgelb.strokewidth = 0
        
def onMouseUpBlue(event):
    global offset
    node = event.node
    #nur, falls Rechteck angeklickt wurde
    if offset != None:
        #offset wieder auf None setzen und das gruene Rechteck wieder anzeigen
        node.releaseEventCapture()
        offset = None;
        obenlinksgruen.fillopacity = 1
        obenlinksgruen.strokewidth = 1


#alle Methoden aktivieren
mitteblau.setEventHandler(avg.CURSORDOWN, avg.MOUSE, onMouseDownBlue)
mitteblau.setEventHandler(avg.CURSORMOTION, avg.MOUSE, onMouseMoveBlue)
mitteblau.setEventHandler(avg.CURSORUP, avg.MOUSE, onMouseUpBlue)
obenlinksgruen.setEventHandler(avg.CURSORDOWN, avg.MOUSE, onMouseDownGreen)