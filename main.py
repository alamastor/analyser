import kivy

from myGraph import MyGraph

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.image import Image
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy.graphics.vertex_instructions import Line, Rectangle
from kivy.graphics import Color
from kivy.graphics.fbo import Fbo
from kivy.graphics.instructions import InstructionGroup
from kivy.properties import StringProperty, ListProperty

import os.path
from PIL import Image as PILImage
from PIL.ImageStat import Stat as imageStat


class Painter(Widget):
    buttonText = ListProperty([str(i + 1) for i in range(15)])
    imageFile = StringProperty('')
    def __init__(self, **kwargs):
        super(Painter, self).__init__(**kwargs)
        self.boxNo = 1
        self.instructions = [InstructionGroup() for _ in range(15)]
        for instruction in self.instructions:
            self.canvas.add(instruction)
        self.xList = [None] * 15
        self.yList = [None] * 15


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            try:
                self.boxHeight = int(self.parent.ids['boxSizeText'].text)
            except ValueError:
                self.boxHeight = 15
                self.parent.ids['boxSizeText'].text = str(self.boxHeight)
            self.instructions[self.boxNo - 1].clear()
            self.parent.refToPainterCanvas = self.canvas.proxy_ref
            h = int(self.boxHeight)
            self.instructions[self.boxNo - 1].add(Color(0, 0, 0, 0.25))
            touch.ud['Rectangle'] = Rectangle(pos=(touch.x - h / 2, touch.y  - h / 2),
                                              size=(h, h))
            self.instructions[self.boxNo - 1].add(touch.ud['Rectangle'])


    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            h = self.boxHeight
            self.instructions[self.boxNo - 1].clear()
            touch.ud['Rectangle'].pos = (touch.x - h / 2, touch.y - h / 2)
            self.instructions[self.boxNo - 1].add(Color(0, 0, 0, 0.25))
            self.instructions[self.boxNo - 1].add(touch.ud['Rectangle'])

    
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.xList[self.boxNo - 1] = touch.x
            self.yList[self.boxNo - 1] = touch.y
            if self.imageFile != '':
                self.readRectangle()


    def readRectangle(self):
        x = self.xList[self.boxNo - 1]
        y = self.yList[self.boxNo - 1]
        image = PILImage.open(self.imageFile)
        image = image.transpose(PILImage.FLIP_TOP_BOTTOM)
        scaled_x = int(x * (image.size[0] / float(self.width)))
        scaled_y = int((y - self.y) * (image.size[1] / float(self.height)))
        scaled_boxWidth = int(self.boxHeight * (image.size[0] / float(self.width)))
        scaled_boxHeight = int(self.boxHeight * (image.size[1] / float(self.height)))
        croppedImage = image.crop((scaled_x, scaled_y,
                                   scaled_x + scaled_boxWidth, scaled_y + scaled_boxHeight))
        color = imageStat(croppedImage).mean
        if image.mode == 'RGB':
            lStr = ('[b]{0}[/b]\nR: {1:03.0f}   G: {2:03.0f}   B: {3:03.0f}')
            self.buttonText[self.boxNo - 1] = lStr.format(self.boxNo, color[0], color[1], color[2])
        elif image.mode == 'RGBA':
            lStr = ('[b]{0}[/b]\nR: {1:03.0f}   G: {2:03.0f}   B: {3:03.0f}   A: {4:03.0f}')
            self.buttonText[self.boxNo - 1] = lStr.format(self.boxNo, color[0], color[1], color[2], color[3])
        else:
            print 'WARNING!: Unsupported color mode - {}'.format(image.mode)
            self.buttonText[self.boxNo - 1] = 'WARNING!: Unsupported color mode - {}'.format(image.mode)


class GraphScreen(Widget):
    pass


class ColorReaderScreen(Widget):
    pass


class FileChooserScreen(Widget):
    pass


class Main(App):
    def build(self):
        self.graphScreen = GraphScreen()
        self.colorReaderScreen = ColorReaderScreen()
        self.fileChooserScreen = FileChooserScreen()
        return self.fileChooserScreen
    
        
    def goto_color_reader(self, imageFile=None):
        self.imageFile = imageFile
        Window.remove_widget(self.fileChooserScreen)
        Window.remove_widget(self.graphScreen)
        Window.add_widget(self.colorReaderScreen)
        if imageFile is not None:
            self.colorReaderScreen.ids['painter'].imageFile = imageFile
            self.imageFile = self.resizeImage(imageFile)
            self.colorReaderScreen.canvas.before.clear()
            with self.colorReaderScreen.canvas.before:
                Rectangle(source=self.imageFile, keep_ratio=True,
                          size=(self.colorReaderScreen.width, self.colorReaderScreen.height*0.75),
                          pos=(self.colorReaderScreen.x, self.colorReaderScreen.height*0.25))


    def goto_graph(self):
        Window.remove_widget(self.colorReaderScreen)
        Window.add_widget(self.graphScreen)


    def resizeImage(self, imageFile):
        basewidth = 800
        img = PILImage.open(imageFile)
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), PILImage.ANTIALIAS)
        newFile = os.path.dirname(imageFile) + '/resized_' + os.path.basename(imageFile)
        img.save(newFile)
        return newFile


if __name__ == '__main__':
    Main().run()
