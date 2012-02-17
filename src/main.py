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

1. Punktevergabe bei geistkontakt implementieren
2. Geistermodus zufaellig aendern (Blau/Normal)
3. Spielfeldabtrennung schoener darstellen 

999. jegliches gehacke entfernen 

'''