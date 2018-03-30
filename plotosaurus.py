import sys
import datetime
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.dockarea import DockArea, Dock
from toon.input import MultiprocessInput as MpI
from toon.input.hand import Hand
# pip install git+https://github.com/aforren1/toon

np.set_printoptions(precision=4, linewidth=150, suppress=True, threshold=1500)

class Dummy():
    def __init__(self):
        pass
    def __enter__(self):
        pass
    def __exit__(self, *args):
        pass

demo = False

# base window, etc.
app = QtGui.QApplication([])
win = QtGui.QMainWindow()
#win.setWindowIcon(QtGui.QIcon('icon.jpg'))
area = DockArea()
win.setCentralWidget(area)
win.resize(1200, 400)
win.setWindowTitle('The Plotosaurus')

d1 = Dock('Forces', size = (1000, 600))
d2 = Dock('Settings', size = (250, 600))
area.addDock(d1, 'left')
area.addDock(d2, 'right')

plotwidget = pg.GraphicsLayoutWidget()
num_plots = 5
plots = list()
curves = list()

for i in range(num_plots):
    plots.append(plotwidget.addPlot())
    #plots[i].setDownsampling(mode='peak')
    plots[i].setClipToView(True)
    plots[i].setRange(yRange=[-2, 2])
    data = np.random.normal(size=200)
    for j in range(3):
        curves.append(plots[i].plot(data, pen=pg.mkPen(color=pg.intColor(j, hues=5, alpha=255, width=3))))

d1.addWidget(plotwidget)

logging = False
log_file_name = ''
def log_and_print(state):
    global logging, log_file_name
    logging = state
    log_file_name = datetime.datetime.now().strftime('log_%Y-%m-%d_%H-%M-%S.txt')

please_center = False
def median_centering():
    global please_center
    please_center = True

setwidget = pg.LayoutWidget()
logging_toggler = QtGui.QCheckBox('Logging')
logging_toggler.stateChanged.connect(log_and_print)
zero_button = QtGui.QPushButton('Center Traces')
zero_button.clicked.connect(median_centering)

setwidget.addWidget(logging_toggler)
setwidget.addWidget(zero_button)
d2.addWidget(setwidget)

centering = None
current_data_view = None
def update():
    global current_data_view, logging, log_file_name, centering, please_center
    if demo:
        data = np.random.random((16, 15))
    else:
        ts, data = dev.read()
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
        current_data_view[-data.shape[0]:,:] = data - centering
    if logging:
        print(data[-1,:])
        with open(log_file_name, 'ab') as f:
            np.savetxt(f, data, fmt='%10.5f', delimiter=',')
    for counter, c in enumerate(curves):
        c.setData(y=current_data_view[:, counter])

if __name__ == '__main__':
    if demo:
        device = Dummy()
    else:
        device = MpI(Hand)
    
    with device as dev:
        win.show()
        timer = pg.QtCore.QTimer()
        timer.timeout.connect(update)
        timer.start(17)
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()
