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
EIGENE!!! bilder fuer die spielelemente erstellen(bricks,boni)
geister scheuchen implementieren
KI fuer geisterverhalten schreiben
bessere fress-effekte (auch fuer geist frisst ball)
geist-schatten fixen
namen ausdenken fuer das spiel

********************* ODOT *******************

The game can now be started directly from game.py




********************* NOTES *******************

please let your event handlers return False to prevent bubbling, also use setEventCapture(id)
please use camelCase when naming methods and fields and let's not use underscores
classnames should begin with a capital letter and also use CamelCase
the todos are prioritized as follows: FIXME > TODO > XXX

'''