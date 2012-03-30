'''
Created on 19.01.2012

@author: 2526240
'''

# ****************** general config ******************
debug = True
pointsToWin = 100
PPM = 20 # number of pixels per meter
TIME_STEP = .013

# ****************** bat config ******************
maxBatSize = 17 # maximal bat size in meters

# ****************** wall config ******************
brickSize = 2 # the size of a brick in meter 
brickLines = 4
maxNumOfRubberBricks = 7

# ****************** bonus config ******************
bonusTime = 3 # the time in seconds a bonus waits for interaction before disappearing
bonusMaximum = 10
# ****************** ball config ******************
maxBalls = 3 # the maximum number of pacmans on the field 
ballRadius = 1.2 # the radius of a pacman in meters

# ****************** ghost config ******************
ghostRadius = 1.8 # the radius of a ghost in meters

# ****************** tutorial config ******************
startingTutorial = 2000
ballTutorial = 10000
tetrisTutorial = 10000
ghostTutorial = 10000
bonusTutorial = 10000
bonusVanishTime = 10000

# ****************** tutorial config ******************

abstractBoniText = ("This is a bonus.<br/>" + 
"Tap on it before your opponent does!<br/>" + 
"Some boni will activate as soon as you tap on them, <br/> " + 
"and some will be stored on your bubbles and glass bricks in your wall.<br/> " + 
"The latter can be activated strategically by tapping on them.<br/> " + 
"The bubble gets destroyed when you activate its bonus.<br/>" + 
"Click on them")


pacShotText = ("This is a decoy.<br/>" + 
"You can launch three pacmans to confuse and distract your opponent.<br/> " + 
"These pacmans do not bring you points, however. ")
                     
stopGhostsText = ("This halts the ghosts for a few moments.") 
flipGhostsText = ("This lets blue ghosts become normal and vice versa.") 
 
towerText = ("This spawns three temporary towers that will shoot red pacmans at your opponent.<br/> " + 
"They will destroy his wall; however, they can be stopped by a bat or a shield. ")
                     
invertPacText = ("This inverts the moving direction of all pacmans.") 

shieldText = ("This spawns a temporary shield that will protect you from almost everything. ")
 
waveText = ("This spawns a wave of energy pellets that will destroy enemy mines and deflect pacmans. <br/> "
+ "However, they will fade upon contact with anything. ")

newBlockText = ("This spawns a random tetris block.<br/> " + "You have three seconds to put it into your wall before it fades.") 

addOwnGhostText = ("This spawns a temporary friendly ghost that will not harm pacmans if they were sent by you. ") 

hideGhostsText = ("This scares ghosts away.<br/> " + 
"They will not bother you until they get called back. ")

resetGhostsText = ("This calls the original four ghosts.<br/> " + 
"They respawn on their original positions. ")

sendGhostsToOtherSideText = ("This sends all ghosts to fly around in your opponents field. ") 

mineText = ("This spawns a mine that looks like a pacman of your color.<br/> " + "It will give you a point if your opponent sends a pacman to collide with it.")

abstractTetrisText = ("You have 10 seconds to drag these blocks into your wall.")
 
