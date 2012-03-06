
from libavg import AVGApp, avg, ui


class Wall (AVGApp):
    def init(self):
        
        self.div = avg.DivNode(parent=self._parentNode,#size=(100,100),
                               elementoutlinecolor='FFFFFF',crop=False)
        self.div1 = avg.DivNode(parent=self.div,size=(25,25),elementoutlinecolor='FFFFFF')
        self.div2 = avg.DivNode(parent=self.div,size=(100,100),pos=(30,30),elementoutlinecolor='FFFFFF')
        
        self.cid = None
        
        ui.DragRecognizer(self.div1,moveHandler=self.onMove)
        ui.DragRecognizer(self.div2,moveHandler=self.onMove)
        
        self.node = avg.ImageNode(parent=self.div, pos=(150, 150))
        self.node.setBitmap(avg.SVG('../data/img/char/glass.svg', False).renderElement('layer1', (100, 100)))
        self.node.intensity = (.5, 1, .5)
        
        self.node1 = avg.ImageNode(parent=self.div, pos=(300, 300))
        self.node1.setBitmap(avg.SVG('../data/img/char/glass.svg', False).renderElement('layer1', (100, 100)))
        self.node1.intensity = (1, .5, .5)
        
    def onStart(self,e):
        if self.cid is None:            
            self.offset = e.pos-self.div.pos
            self.cid = e.cursorid
            self.div.setEventCapture(self.cid)
            print 'started at',self.div.pos,'with offset',self.offset,'capturing',self.cid
        
    def onMove(self,e,o):
        self.div.pos += o
            
    def onUp(self,e):
        if self.cid == e.cursorid:
            print 'releasing',self.cid
            self.div.releaseEventCapture(self.cid)
            self.cid = None
        
if __name__ == '__main__':
    Wall.start (resolution = (1024, 768))