import argparse

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from toon.input import MpDevice
from toon.input.hand import Hand
from demodev import SingleResp


class LivePlot(pg.GraphicsLayoutWidget):
    def __init__(self, device):
        super(LivePlot, self).__init__()
        self.plot = self.addPlot()
        self.curves = []
        self.device = MpDevice(device)
        self.current_data = None
        for i in range(15):
            color = pg.intColor(i, hues=15, alpha=255, width=3)
            self.curves.append(self.plot.plot((0, 0), pen=pg.mkPen(color=color)))
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(0)
        self.playing = True

    def update(self):
        pos = self.device.read()
        if pos is None:
            return
        if self.current_data is None:
            self.current_data = pos
        elif self.current_data.shape[0] < 1000:
            self.current_data = np.vstack((self.current_data, pos))
        else:
            self.current_data = np.roll(self.current_data, -pos.shape[0], axis=0)
            self.current_data[-pos.shape[0]:, :] = pos
        if self.playing:
            for counter, c in enumerate(self.curves):
                c.setData(y=self.current_data[:, counter])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', default=False,
                        action='store_true', help='Demo mode?')
    args = parser.parse_args()
    if args.demo:
        # demo device
        device = SingleResp()
    else:
        device = Hand()
    app = QtGui.QApplication([])
    w = QtGui.QWidget()
    liveplot = LivePlot(device)

    pause_button = QtGui.QPushButton('Pause')

    def on_click():
        liveplot.playing = not liveplot.playing

    pause_button.clicked.connect(on_click)
    layout = QtGui.QGridLayout()
    w.setLayout(layout)
    layout.addWidget(liveplot, 0, 0, 3, 3)
    layout.addWidget(pause_button, 0, 1)
    w.show()
    with liveplot.device:
        app.exec_()
