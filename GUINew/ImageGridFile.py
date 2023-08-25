
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtCore import Qt, qInstallMessageHandler, QObject, QThread, pyqtSignal
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
    def __init__(self, item_size = 200, text_enabled = True, loading_percent_callback = None):
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
        self.loading_percent_callback = loading_percent_callback

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
        data_len = len(data)
        for d in enumerate(data):
            self.add_image(d)
            if self.loading_percent_callback is not None:
                self.loading_percent_callback(100 * d[0]/max(data_len, 1))

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
    
    def add_to_grid(self, image : ImagePreview):
        image.parent = self.content
        i = self.layout_gird.count()
        self.layout_gird.addWidget(image, i // self.max_collum_count, i % self.max_collum_count)

    def done_adding(self):
        print("Done")

    def add_images_mt(self, data:list[ImageData]):
        self.removeAllImages()
        self.image_adder = ImageAddWorker(data, self)
        self.image_adder.progress.connect(self.loading_percent_callback)
        self.image_adder.add.connect(self.add_to_grid)
        self.image_adder.done.connect(self.done_adding)
        self.image_adder.done.connect(self.image_adder.quit)
        self.image_adder.run()
    
class ImageAddWorker(QThread):
    done = pyqtSignal()
    progress = pyqtSignal(int)
    add = pyqtSignal(ImagePreview)
    def __init__(self, data : [ImageData], image_grid : ImageGrid = None):
        super().__init__()
        self.data = data
        self.image_grid = image_grid

    def run(self):
        data_len = len(self.data)
        for i, d in enumerate(self.data):
            classes = reduce((lambda a, b: a+" " +b.className), d.classes, "")
            ip = ImagePreview(d.orgImage, description=f"Classes: {classes}", text_enabled=self.text_enabled)
            if self.image_grid is not None:
                self.image_grid.add_to_grid(ip)
            else:
                self.add.emit(ip)
            if i % 10 == 0:
                self.progress.emit(int(100 * i / data_len))
        self.done.emit()
