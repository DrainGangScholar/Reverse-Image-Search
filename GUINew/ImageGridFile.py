
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
import typing
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
import sys

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from GUINew.ImagePreviewFile import ImagePreview

from ImageAnalyzationModule.ImageAnalyzationFile import *
from GUI.GUIFunctions import *

class ImageGrid(QScrollArea):
    def __init__(self, item_size = 200, text_enabled = True):
        super().__init__()
        self.content = QWidget()
        self.layout_gird = QGridLayout()
        self.layout_gird.setSpacing(0)
        self.layout_gird.setContentsMargins(0,0,0,0)
        self.text_enabled = text_enabled
        self.item_size = item_size + ( int(item_size*2/3) if text_enabled else 0)
        self.max_collum_count = max(self.content.width() // self.item_size, 1)

        self.content.setLayout(self.layout_gird)
        self.setWidget(self.content)
        self.setWidgetResizable(True)
        self.old_resize = self.resizeEvent
        self.resizeEvent = self.on_resize

    def on_resize(self, event):
        self.old_resize(event)
        self.content.setMaximumWidth(self.width())
        old_collum_count = self.max_collum_count
        self.max_collum_count = max(self.content.width() // self.item_size, 1)

        if self.max_collum_count == old_collum_count:
            return
        
        # widgets = list(enumerate(self.layout_gird))
        widgets = [(i, self.layout_gird.itemAt(i).widget()) for i in range(self.layout_gird.count())]
                       
        while self.layout_gird.count() > 0:
            item = self.layout_gird.itemAt(0)
            if item.widget():
                self.layout_gird.removeWidget(item.widget())
            else:
                self.layout_gird.removeItem(item)
            
        for i, widget in widgets:
            self.layout_gird.addWidget(widget, i // self.max_collum_count, i % self.max_collum_count)
        return

    def removeAllImages(self):
        while self.layout_gird.count():
            item = self.layout_gird.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


    def addImages(self, data : list[ImageData]):
        self.removeAllImages()
        for d in enumerate(data):
            self.add_image(d)

    def add_image(self, data):
        i, d = None, None
        if type(data) is tuple:
            i,d =data
        else:
            d = data
            i = self.layout_gird.count()
        classes = reduce((lambda a, b: a+" " +b.className), d.classes, "")
        ip = ImagePreview(d.orgImage, description=f"Classes: {classes}", text_enabled=self.text_enabled)
        self.layout_gird.addWidget(ip, i // self.max_collum_count, i % self.max_collum_count)