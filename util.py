from kivy.app import App
from kivy.clock import Clock
from kivy.uix.popup import Popup

from plyer import camera

from functools import partial
from PIL import Image as PILImage
import os
from types import *


def channelIndexFromName(measuredChannel):
    if measuredChannel == 'red':
        return 0
    if measuredChannel == 'green':
        return 1
    if measuredChannel == 'blue':
        return 2
    raise RuntimeError('{} is not a valid channel '
                       'name.'.format(measuredChannel))


def take_photo(filepath):
    try:
        print 'taking picture'
        camera.take_picture(filepath, camera_callback)
    except NotImplementedError:
        popup = MsgPopup(msg="This feature has not yet been "
                             "implemented for this platform.")
        popup.open()


def camera_callback(imageFile, **kwargs):
    app = App.get_running_app()
    print 'got camera callback'
    PILImage.open(imageFile).resize((800, 600)).save(imageFile)
    Clock.schedule_once(partial(app.goto_color_reader_screen, imageFile, 0.3))
    return False


class MsgPopup(Popup):
    def __init__(self, msg):
        super(MsgPopup, self).__init__()
        self.ids.message_label.text = msg


class CalibrationCurve(object):
    def __init__(self, mode=None, M=None, C=None, R2=None, channel=None,
                 pointsCount=None, file=None, status='OK',
                 blankVal=None):
        assert status in ['OK', 'NoBlank', 'NotEnoughConcentrations']
        if file is not None:
            assert mode is None
            assert M is None
            assert C is None
            assert R2 is None
            assert pointsCount is None
            self.readCalibFile(file)
        elif status == 'OK':
            assert mode in ['Blank Normalize', 'Surrounds Normalize']
            assert type(M) is FloatType
            assert type(C) is FloatType
            assert type(R2) is FloatType
            assert channel in ['red', 'green', 'blue']
            self.mode = mode
            self.M = M
            self.C = C
            self.R2 = R2
            self.channel = channel
            self.pointsCount = pointsCount
            self.status = status
            self.blankVal = blankVal
        else:
            self.status = status

    def readCalibFile(self, calibFile):
        with open(calibFile, 'r') as f:
            self.status = f.next().split()[1]
            if self.status == 'OK':
                self.mode = f.next().split(':')[1].strip()
                self.M = float(f.next().split()[1])
                self.C = float(f.next().split()[1])
                self.R2 = float(f.next().split()[1])
                self.channel = f.next().split()[1]
                self.pointsCount = int(f.next().split()[1])
                if self.mode == 'Blank Normalize':
                    self.blankVal = float(f.next().split(':')[1])
                else:
                    self.blankVal = None

    def writeCalibFile(self, calibFile):
        with open(calibFile, 'wb') as f:
            if self.status == 'OK':
                f.write('Status: {}\n'.format(self.status))
                f.write('Mode: {}\n'.format(self.mode))
                f.write('M: {}\n'.format(self.M))
                f.write('C: {}\n'.format(self.C))
                f.write('R2: {}\n'.format(self.R2))
                f.write('Channel: {}\n'.format(self.channel))
                f.write('PointsCount: {}\n'.format(self.pointsCount))
                if self.mode == 'Blank Normalize':
                    f.write('Blank: {}\n'.format(self.blankVal))
            else:
                f.write(self.status + '\n')