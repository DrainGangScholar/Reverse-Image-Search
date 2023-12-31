import multiprocessing as mp
import sys
from GUI import GLUE
from DB.SqliteDB import ImageDB
from ImageAnalyzationModule.ImageAnalyzationFile import ImageAnalyzation, AnalyzationType
from GUI.VideoPlayerFile_old import VideoPlayer
#from GUI.VideoPlayerFile import VideoPlayer
from PyQt5.QtWidgets import (
    QApplication
)
if __name__=='__main__':
    mp.set_start_method('spawn')
    img_analyzer=ImageAnalyzation("yolov8s.pt", device="cuda", analyzationType=AnalyzationType.CoderDecoder, coderDecoderModel="1A-27")
    img_db=ImageDB()
    app = QApplication(sys.argv)
    window = GLUE.GUI(img_db,img_analyzer)
    window.show()
    sys.exit(app.exec_())