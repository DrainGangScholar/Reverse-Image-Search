import os
import subprocess
from PyQt5.QtGui import *
from PyQt5.QtCore import QDir, Qt, QUrl, QSize, QPoint, pyqtSignal
import PyQt5.QtCore as QtCore
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QVideoProbe
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QCursor
import cv2



class VideoPlayer(QWidget):
    def __init__(self, fileName="", data: list = None, parent=None, item_size=200, start_frame= 0):
        super(VideoPlayer, self).__init__(parent)
        self.setWindowIcon(QIcon(".\AppImages\search.png"))
        self.setWindowTitle("Kimaris : Video Player")
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.collum_number = self.width() // item_size
        self.item_size = item_size
        btnSize = QSize(16, 16)
        videoWidget = QVideoWidget()

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setFixedHeight(24)
        self.playButton.setIconSize(btnSize)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.open_folder = QPushButton()
        self.open_folder.setEnabled(True)
        self.open_folder.setFixedHeight(24)
        self.open_folder.setIconSize(btnSize)
        self.open_folder.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.open_folder.clicked.connect(self.show_in_explorer)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)
        self.positionSlider.sliderPressed.connect(self.onSliderClicked)

        self.statusBar = QStatusBar()
        self.statusBar.setFont(QFont("Noto Sans", 7))
        self.statusBar.setFixedHeight(20)

        self.duration = QLabel()
            
        self.duration.setText("00:00/00:00")
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addWidget(self.duration)
        controlLayout.addWidget(self.open_folder)

        # Adding all the video frames

        self.scroll_area = QScrollArea()
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.content_frames = QWidget()
        self.content_layout = QGridLayout()
        self.content_layout.setRowMinimumHeight(0, item_size)
        self.content_layout.setSpacing(0)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.old_resize_frames = self.resizeEvent
        self.scroll_area.resizeEvent = self.resize_frames

        data.sort(key=lambda x: int(x[1]))

        for ed in enumerate(data):
            d = ed[1]
            i = ed[0]
            vpi = VideoPlayerItem(d[1], d[0], size=(item_size, item_size))
            vpi.clicked.connect(self.item_click_position_change)
            self.content_layout.addWidget(
                vpi, i // self.collum_number, i % self.collum_number
            )

        self.content_frames.setLayout(self.content_layout)
        self.scroll_area.setWidget(self.content_frames)
        self.scroll_area.setWidgetResizable(True)

        layout = QVBoxLayout()
        layout.addWidget(videoWidget, stretch=6)
        layout.addLayout(controlLayout, stretch=1)
        layout.addWidget(self.statusBar, stretch=2)
        layout.addWidget(self.scroll_area, stretch=4)

        self.setLayout(layout)

        self.mediaPlayer.setVideoOutput(videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)
        self.statusBar.showMessage("Ready")

        self.file_name = fileName
        self.file_folder_path = os.path.dirname(fileName)
        print(self.file_folder_path)
        self.fps = None
        if fileName != "":
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
            self.playButton.setEnabled(True)
            self.statusBar.showMessage(fileName)
            cam = cv2.VideoCapture(fileName)
            self.fps = int(cam.get(cv2.CAP_PROP_FPS))

            self.play()
        self.item_click_position_change(int(data[0][1]) if start_frame == 0 else start_frame)
        self.resize_frames(None)

    def show_in_explorer(self):
        subprocess.Popen(['explorer.exe', '/select,', os.path.normpath(self.file_name)])
        # os.startfile(self.file_folder_path)

    @QtCore.pyqtSlot(int)
    def item_click_position_change(self, frame_num: int):
        fps = int(self.fps if self.fps is not None and self.fps > 0 else 30)
        self.mediaPlayer.setPosition((int(frame_num) // fps) * 1000)

    def resize_frames(self, event):
        if event is not None:
            self.old_resize_frames(event)
            
        self.content_frames.setMinimumWidth(self.scroll_area.width())
        old_collum = self.collum_number
        self.collum_number = max(self.scroll_area.width() // self.item_size, 1)
        if old_collum == self.collum_number:
            return

        widgets = [
            (i, self.content_layout.itemAt(i).widget())
            for i in range(self.content_layout.count())
        ]
        while self.content_layout.count() > 0:
            item = self.content_layout.itemAt(0)
            if item.widget():
                self.content_layout.removeWidget(item.widget())
            else:
                self.content_layout.removeItem(item)

        for i, widget in widgets:
            self.content_layout.addWidget(
                widget, i // self.collum_number, i % self.collum_number
            )

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            # self.mediaPlayer.setPosition(500)
            self.mediaPlayer.play()

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)
        duration_sec = self.mediaPlayer.duration()//1000
        duration_min = duration_sec // 60
        duration_sec = duration_sec % 60
        position = position // 1000
        pos_min = position // 60
        pos_sec = position % 60
        self.duration.setText(f"{pos_min}:{pos_sec}/{duration_min}:{duration_sec}")

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(int(position))

    def handleError(self):
        self.playButton.setEnabled(False)
        self.statusBar.showMessage("Error: " + self.mediaPlayer.errorString())

    def onSliderClicked(self):
        click_position = (
            QCursor.pos().x() - self.positionSlider.mapToGlobal(QPoint(0, 0)).x()
        )
        max_position = self.positionSlider.width()
        value = (click_position / max_position) * self.positionSlider.maximum()
        self.setPosition(value)

    def closeEvent(self, event):
        self.mediaPlayer.stop()
        event.accept()

    def closePlayer(self):
        self.mediaPlayer.stop()

class VideoPlayerItem(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, frame_num=0, image: QPixmap = None, size=(200, 200)):
        super().__init__()
        self.frame_num = frame_num
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image = image.scaled(
            size[0],
            size[1],
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            transformMode=Qt.TransformationMode.FastTransformation,
        )
        self.image_label.setPixmap(self.image)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layot = QHBoxLayout()
        self.main_layot.addWidget(self.image_label)
        self.setLayout(self.main_layot)
        self.setMaximumWidth(size[0])
        self.setMinimumWidth(size[0])
        self.setMaximumHeight(size[1])
        self.setMinimumHeight(size[1])
        self.mouseDoubleClickEvent = self.double_click_event
        self.setContentsMargins(0, 0, 0, 0)

    def enterEvent(self, a0):
        super().enterEvent(a0)
        color = QColor(0x21, 0x47, 0x6B, 120)
        mod_px = self.image.copy()
        painter = QPainter(mod_px)
        w, h = mod_px.width(), mod_px.height()
        painter.fillRect(0, 0, w, h, color)
        painter.end()
        self.image_label.setPixmap(mod_px)
        self.image_label.setStyleSheet("background-color: #21476b;")

    def leaveEvent(self, a0) -> None:
        super().leaveEvent(a0)
        self.setStyleSheet("background-color: #EFEFEF;")
        self.image_label.setStyleSheet("background-color: #000000;")
        self.image_label.setPixmap(self.image)

    def double_click_event(self, event):
        self.clicked.emit(int(self.frame_num))
