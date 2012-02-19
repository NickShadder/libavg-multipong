'''
Created on 15.02.2012

@author: 2526240
'''

import sys
import config
from game import Game

if __name__ == '__main__':
    if config.debug: 
        print "DEBUG: Starting Application"
    Game.start(sys.argv)
    if config.debug:
        print "DEBUG: Leaving main" 
        
'''
********************* TODO *******************

jegliches gehacke entfernen
agv rendering reorganisieren
kollisionen in pybox schreiben
punktevergabe bei geistkontakt implementieren
in welchem zustand soll ein geist nach dem Tod erscheinen (fressbar oder nicht? )
spielfeldabtrennung schoener darstellen  
EIGENE!!! bilder fuer die spielelemente erstellen(pacman, ghosts, bricks)
namen ausdenken fuer das spiel

********************* ODOT *******************

The game can now be started directly from game.py




********************* NOTES *******************

please let your event handlers return False to prevent bubbling, also use setEventCapture(id)
please use camelCase when naming methods and fields and let's not use underscores
classnames should begin with a capital letter and also use CamelCase
the todos are prioritized as follows: FIXME > TODO > XXX

'''