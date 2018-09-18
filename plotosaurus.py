import argparse
import ctypes
import datetime
import sys

import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
from pyqtgraph.Qt import QtCore, QtGui

from toon.input import MultiprocessInput as MpI
from toon.input.fake import FakeInput
from calib_hand import Hand

np.set_printoptions(precision=4, linewidth=150, suppress=True)

# base window, etc.
app = QtGui.QApplication([])
win = QtGui.QMainWindow()

area = DockArea()
win.setCentralWidget(area)
win.resize(1200, 400)
win.setWindowTitle('The Plotosaurus')

d1 = Dock('Forces', size=(1000, 600))
d2 = Dock('Settings', size=(250, 600))
area.addDock(d1, 'left')
area.addDock(d2, 'right')

plotwidget = pg.GraphicsLayoutWidget()
num_plots = 5
plots = list()
curves = list()

for i in range(num_plots):
    plots.append(plotwidget.addPlot())
    # plots[i].setClipToView(True)
    #plots[i].setRange(yRange=[-1, 1])
    data = np.random.normal(size=200)
    for j in range(3):
        curves.append(plots[i].plot(data, pen=pg.mkPen(
            color=pg.intColor(j, hues=5, alpha=255, width=3))))

d1.addWidget(plotwidget)

logging = False
log_file_name = ''


def stop_logging():
    global logging
    logging = False
    logging_toggler.setText('Log for 5 seconds')


timer = QtCore.QTimer()


def log_and_print():
    global logging, log_file_name
    logging = True
    log_file_name = textbox.text(
    ) + datetime.datetime.now().strftime('_%Y-%m-%d_%H-%M-%S') + '.txt'
    logging_toggler.setText('Now logging')
    timer.singleShot(5000, stop_logging)


please_center = False


def median_centering():
    global please_center
    please_center = True


setwidget = pg.LayoutWidget()
logging_toggler = QtGui.QPushButton('Log for 5 seconds')
logging_toggler.clicked.connect(log_and_print)
zero_button = QtGui.QPushButton('Center Traces')
zero_button.clicked.connect(median_centering)

setwidget.addWidget(logging_toggler)
setwidget.addWidget(zero_button)
d2.addWidget(setwidget)
textbox = QtGui.QLineEdit()
setwidget.addWidget(textbox)

centering = None
current_data_view = None


def update():
    global current_data_view, logging, log_file_name, centering, please_center
    ts, data = device.read()
    if data is None:
        return
    if please_center:
        please_center = False
        centering = np.median(data, axis=0)
    if current_data_view is None:
        current_data_view = data
        centering = np.median(data, axis=0)
    elif current_data_view.shape[0] < 1000:
        current_data_view = np.vstack((current_data_view, data - centering))
    else:
        current_data_view = np.roll(current_data_view, -data.shape[0], axis=0)
        current_data_view[-data.shape[0]:, :] = data - centering
    if logging:
        print(data[-1, :])
        with open(log_file_name, 'ab') as f:
            np.savetxt(f, data, fmt='%10.5f', delimiter=',')
    for counter, c in enumerate(curves):
        c.setData(y=current_data_view[:, counter])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', help='Demo mode or not',
                        type=bool, default=False)
    args = parser.parse_args()
    print(args)
    if False:
        device = MpI(FakeInput, sampling_frequency=1000,
                     data_shape=[[15]], data_type=[ctypes.c_double])
    else:
        device = MpI(Hand,
                     calibration_files=['calibs/cal_mat_18.mat',  # thumb
                                        'calibs/cal_mat_14.mat',
                                        'calibs/cal_mat_17.mat',
                                        'calibs/cal_mat_13.mat',
                                        'calibs/cal_mat_15.mat'])

    device.start()
    win.show()
    timer = pg.QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(17)
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
    device.stop()
