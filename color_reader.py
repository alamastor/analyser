import kivy

from kivy.app import App
from kivy.uix.widget import Widget

from kivy.clock import Clock
import os
from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics import Color
from kivy.core.image import Image
import kivy.metrics as metrics

from kivy.properties import StringProperty,\
                            ListProperty,\
                            ReferenceListProperty,\
                            NumericProperty,\
                            ObjectProperty,\
                            BooleanProperty

from kivy.graphics.instructions import InstructionGroup
from analyser_util import channelIndexFromName 
from PIL import Image as PILImage
from PIL.ImageStat import Stat as imageStat
import math

class ColorReaderSpot(object):
    def __init__(self, idNo = None, type='std', conc=0.0):
        self.idNo = idNo
        self.sampleGrp = None
        self.type = type
        self.conc = conc
        # canvas instruction group
        self.instGrp = InstructionGroup()
        self.colorVal = None
        self.colorMode = None
        self.A = None
        self.spotColor = Color(1, 0, 0, 0.5)
        self.surroundsSpotColor = Color(0, 0, 0, 0.25)
        self.absorb = None
        self.exclude = False


    def updateText(self):
        app = App.get_running_app()
        channelIndex = channelIndexFromName(app.measuredChannel)
        assert self.type in ['std', 'sample']
        if self.type == 'std' and self.conc is not None:
            typeText = 'Std ' + str(self.conc)
        elif self.type == 'sample':
            typeText = 'Sample {0}-{1}'.format(self.sampleGrp, self.idNo)

        if self.colorVal is not None:
            text = '[b]{0}[/b]'.format(typeText)
            if self.colorMode == 'RGB':
                print 'spot color type is RGB'
                lStr = '\nR: {0:03.0f}   G: {1:03.0f}   B: {2:03.0f}\n'
                text = text + lStr.format(self.colorVal[0], self.colorVal[1],
                                          self.colorVal[2])
            elif self.colorMode == 'RGBA':
                lStr = ('\nR: {0:03.0f}   G: {1:03.0f}   '
                        'B: {2:03.0f}   A: {3:03.0f}')
                text = text + lStr.format(self.colorVal[0], self.colorVal[1],
                                          self.colorVal[2], self.colorVal[3])
            elif self.colorMode is None:
                print 'programming error color mode not set'
                text = 'color mode not set'
            else:
                print 'unknown color format'
                text = 'unknown color format'

            assert app.analysisMode in ['Blank Normalize',
                                        'Surrounds Normalize']
            if app.analysisMode == 'Blank Normalize':
                pass
            elif app.analysisMode == 'Surrounds Normalize':
                self.absorb = -math.log10(self.colorVal[channelIndex] / surroundsVal)
                lStr = '\nBlank: {4:03.0f}  Absorb: {5:05.3f}'
                text = text + lStr.format(self.absorb, self.surroundsVal)
        else:
            text = '[b]{0}[/b]'.format(typeText)
        return text


    def addMainSpot(self, size, X, Y):
        self.instGrp.clear()
        self.instGrp.add(self.spotColor)
        self.instGrp.add(Rectangle(size=(size, size), pos=(X, Y)))


    def addSurrondsSpots(self, size=2.5):
        self.instGrp.children = self.instGrp.children[:3]
        size = metrics.dp(size)
        mainSize = self.instGrp.children[2].size[0]
        x = self.instGrp.children[2].pos[0] + mainSize / 2 - size / 2
        y = self.instGrp.children[2].pos[1] + mainSize / 2 - size / 2
        self.instGrp.add(self.blankSpotColor)
        self.instGrp.add(Rectangle(size=(size, size), pos=(x, y)))
        self.instGrp.add(Rectangle(size=(size, size), pos=(x, y)))
        self.instGrp.add(Rectangle(size=(size, size), pos=(x, y)))
        self.instGrp.add(Rectangle(size=(size, size), pos=(x, y)))


class ColorReader(Widget):
    spots = ListProperty([])
    imageFile = StringProperty('')
    spotCount = NumericProperty(15)
    currentSpot = ObjectProperty(None)
    currentSpotType = StringProperty('std')
    currentSpotSize = NumericProperty(15)
    currentSpotConc = NumericProperty(0.0)

    text1 = StringProperty('1')
    text2 = StringProperty('2')
    text3 = StringProperty('3')
    text4 = StringProperty('4')
    text5 = StringProperty('5')
    text6 = StringProperty('6')
    text7 = StringProperty('7')
    text8 = StringProperty('8')
    text9 = StringProperty('9')
    text10 = StringProperty('10')
    text11 = StringProperty('11')
    text12 = StringProperty('12')
    text13 = StringProperty('13')
    text14 = StringProperty('14')
    text15 = StringProperty('15')
    spotButtonText = ReferenceListProperty(text1,
                                           text2,
                                           text3,
                                           text4,
                                           text5,
                                           text6,
                                           text7,
                                           text8,
                                           text9,
                                           text10,
                                           text11,
                                           text12,
                                           text13,
                                           text14,
                                           text15)


    def __init__(self, **kwargs):
        super(ColorReader, self).__init__(**kwargs)
        self.spots = [ColorReaderSpot(idNo=i+1) for i in range(self.spotCount)]
        for spot in self.spots:
            self.canvas.add(spot.instGrp)
        self.analysisImage = None
        self.currentSpot = self.spots[0]


    def initialDraw(self):
        print 'in initial draw'
        print 'image file is ', self.imageFile
        print 'in dir', os.listdir(os.path.dirname(self.imageFile))
        self.analysisImage = PILImage.open(self.imageFile)
        self.analysisImage = self.analysisImage.transpose(\
            PILImage.FLIP_TOP_BOTTOM)
        print 'opening image file:', self.imageFile
        for spot in self.spots:
            if len(spot.instGrp.children) > 1:
                assert len(spot.instGrp.children) == 3 or len(spot.instGrp.children) == 12
                spot.colorMode = self.analysisImage.mode
                if spot.type is None:
                    spot.type = self.currentSpotType
                    spot.conc = self.currentSpotConc
                self.readSpot(self.analysisImage, spot)
                self.scanSurroundsSpots(self.analysisImage, spot)
                buttonStr = spot.updateText()
                self.spotButtonText[spot.idNo - 1] = buttonStr 


    def updateSpotSize(self, spotSize):
        try:
            self.currentSpotSize = int(spotSize)
        except ValueError:
            pass


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_down'
            size = metrics.dp(self.currentSpotSize)
            self.currentSpot.addMainSpot(size,
                                         touch.x - size / 2,
                                         touch.y - size / 2)


    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_move'
            size = metrics.dp(self.currentSpotSize)
            self.currentSpot.addMainSpot(size,
                                         touch.x - size / 2,
                                         touch.y - size / 2)


    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_up'
            self.currentSpot.type = self.currentSpotType
            self.currentSpot.conc = self.currentSpotConc
            self.readSpot(self.analysisImage, self.currentSpot)
            self.scanSurroundsSpots(self.analysisImage, self.currentSpot)
            buttonStr = self.currentSpot.updateText()
            self.spotButtonText[self.currentSpot.idNo - 1] = buttonStr


    def startMoveBox(self, horiz, vert):
        self.horiz = horiz
        self.vert = vert
        self.moveBox()
        Clock.schedule_interval(self.moveBox, 0.1)


    def stopMoveBox(self):
        Clock.unschedule(self.moveBox)


    def scanAllSpots(self, channel):
        for spot in self.spots:
            self.scanRegion(spot, channel)


    def scanRegion(self, spot, channel):
        scanRangeLow = int(metrics.dp(15))
        scanResLow = int(metrics.dp(5))
        scanRangeHigh = int(metrics.dp(2.5))
        scanResHigh = int(metrics.dp(1))
        channelIndex = channelIndexFromName(channel)
        checkedSpots = []
        pos = spot.instGrp.children[2].pos
        for x in range(int(pos[0] - scanRangeLow),
                       int(pos[0] + scanRangeLow), scanResLow):
            for y in range(int(pos[1] - scanRangeLow),
                           int(pos[1] + scanRangeLow), scanResLow):
                spot.instGrp.children[2].pos = (x, y)
                self.readSpot(self.analysisImage, spot)
                checkedSpots.append((spot.colorVal[channelIndex], x, y))
        posGrp = min(checkedSpots)
        pos = (posGrp[1], posGrp[2])
        checkedSpots = []
        print 'low', pos
        for x in range(int(pos[0] - scanRangeHigh),
                       int(pos[0] + scanRangeHigh), scanResHigh):
            for y in range(int(pos[1] - scanRangeHigh),
                           int(pos[1] + scanRangeHigh), scanResHigh):
                spot.instGrp.children[2].pos = (x, y)
                self.readSpot(self.analysisImage, spot)
                checkedSpots.append((spot.colorVal[channelIndex], x, y))
        posGrp = min(checkedSpots)
        pos = (posGrp[1], posGrp[2])
        print 'high', pos
        size = spot.instGrp.children[2].size[0]
        spot.addMainSpot(size, pos[0], pos[1])
        self.readSpot(self.analysisImage, spot)
        self.scanSurroundsSpots(self.analysisImage, spot)
        buttonStr = spot.updateText()
        self.spotButtonText[spot.idNo - 1] = buttonStr 


    def moveBox(self, *args):
        horiz = self.horiz
        vert = self.vert
        assert len(self.currentSpot.instGrp.children) == 3 or\
               len(self.currentSpot.instGrp.children) == 12
        for x in self.currentSpot.instGrp.children:
            if str(type(x)) == "<type 'kivy.graphics.vertex_instructions.Rectangle'>":
                x.pos = (x.pos[0] + horiz, x.pos[1] + vert)
        self.readSpot(self.analysisImage, self.currentSpot)
        self.scanSurroundsSpots(self.analysisImage, self.currentSpot)
        buttonStr = self.currentSpot.updateText()
        self.spotButtonText[self.currentSpot.idNo - 1] = buttonStr


    def readSpot(self, image, spot):
        spotSize = spot.instGrp.children[2].size[0]
        spotX = spot.instGrp.children[2].pos[0]
        spotY = spot.instGrp.children[2].pos[1]
        scaled_x = int((spotX - self.x) * (image.size[0] / float(self.width)))
        scaled_y = int((spotY - self.y) * (image.size[1] / float(self.height)))
        scaled_spotWidth = max(int(spotSize * (image.size[0] / float(self.width))), 1)
        scaled_spotHeight = max(int(spotSize * (image.size[1] / float(self.height))), 1)
        croppedImage = image.crop((scaled_x, scaled_y,
                                   scaled_x + scaled_spotWidth,
                                   scaled_y + scaled_spotHeight))
        color = imageStat(croppedImage).mean
        spot.colorVal = color
        spot.colorMode = image.mode


    def scanSurroundsSpots(self, image, spot, scanRange=40):
        app = App.get_running_app()
        if app.analysisMode != "Surrounds Normalize":
            return
        spot.addSurroundsSpots()
        scanRange = int(metrics.dp(scanRange))
        channelIndex = channelIndexFromName(app.measuredChannel)
        maxValList = []
        for i in [(5, -1, 0), (7, 0, 1), (9, 1, 0), (11, 0, -1)]:
            colorValsList = []
            spotSize = spot.instGrp.children[i[0]].size[0]
            scaled_spotWidth = max(int(spotSize * (image.size[0] / float(self.width))), 1)
            scaled_spotHeight = max(int(spotSize * (image.size[1] / float(self.height))), 1)
            # low res scan
            for j in range(0, scanRange, int(scanRange / 5)):
                spotX = spot.instGrp.children[i[0]].pos[0] + j * i[1]
                spotY = spot.instGrp.children[i[0]].pos[1] + j * i[2]
                scaled_x = int((spotX - self.x) * (image.size[0] / float(self.width)))
                scaled_y = int((spotY - self.y) * (image.size[1] / float(self.height)))
                croppedImage = image.crop((scaled_x, scaled_y,
                                           scaled_x + scaled_spotWidth,
                                           scaled_y + scaled_spotHeight))
                colorValsList.append((imageStat(croppedImage).mean[channelIndex], spotX, spotY))
            maxVal = max(colorValsList)
            print maxVal
            maxValList.append(maxVal[0])
            spot.instGrp.children[i[0]].pos = (maxVal[1], maxVal[2])

            # high res scan
            for j in range(6):
                spotX = spot.instGrp.children[i[0]].pos[0] - 3+ j * i[1]
                spotY = spot.instGrp.children[i[0]].pos[1] -3 + j * i[2]
                scaled_x = int((spotX - self.x) * (image.size[0] / float(self.width)))
                scaled_y = int((spotY - self.y) * (image.size[1] / float(self.height)))
                croppedImage = image.crop((scaled_x, scaled_y,
                                           scaled_x + scaled_spotWidth,
                                           scaled_y + scaled_spotHeight))
                colorValsList.append((imageStat(croppedImage).mean[channelIndex], spotX, spotY))
            maxVal = max(colorValsList)
            print maxVal
            maxValList.append(maxVal[0])
            spot.instGrp.children[i[0]].pos = (maxVal[1], maxVal[2])
        spot.surroundsVal = sum(maxValList) / len(maxValList)
        print 'ave blank', spot.surroundsVal


    def updateSpotConc(self, spot, conc):
        spot.conc = conc
        buttonStr = spot.updateText()
        self.spotButtonText[spot.idNo - 1] = buttonStr 


class CalibrationScreen(Widget):
    tex = ObjectProperty(None, allownone=True)


class SampleScreen(Widget):
    tex = ObjectProperty(None, allownone=True)
    sampleGrp = NumericProperty(1)


    def updateSpotGrps(self):
        print 'sample grp is {}'.format(self.sampleGrp)
        for spot in self.ids['colorReader'].spots:
            spot.sampleGrp = self.sampleGrp
